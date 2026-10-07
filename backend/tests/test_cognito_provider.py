"""CognitoIdentityProvider against a stubbed boto3 client: the right calls, and errors mapped right.

No AWS: botocore's Stubber answers, and the JWKS client is a fake holding a local key.
"""

import time

import boto3
import jwt
import pytest
from botocore.stub import ANY, Stubber
from cryptography.hazmat.primitives.asymmetric import rsa

from app.exceptions import (
    EmailAlreadyRegistered,
    IdentityUnavailable,
    InvalidCredentials,
    PasswordRejected,
    Unauthenticated,
)
from app.services.identity import CognitoIdentityProvider

POOL = "sa-east-1_TestPool"
CLIENT = "testclientid"
ISSUER = f"https://cognito-idp.sa-east-1.amazonaws.com/{POOL}"
SUB = "11111111-2222-3333-4444-555555555555"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _FakeJwks:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, token):
        return self


@pytest.fixture()
def cognito():
    client = boto3.client(
        "cognito-idp", region_name="sa-east-1", aws_access_key_id="x", aws_secret_access_key="x"
    )
    stubber = Stubber(client)
    provider = CognitoIdentityProvider(
        "sa-east-1", POOL, CLIENT, profile="nureon", client=client, jwks_client=_FakeJwks(KEY.public_key())
    )
    with stubber:
        yield provider, stubber
        stubber.assert_no_pending_responses()


def _created(email="a@example.test"):
    return {
        "User": {
            "Username": SUB,
            "Attributes": [{"Name": "sub", "Value": SUB}, {"Name": "email", "Value": email}],
        }
    }


def test_create_user_creates_suppressed_and_sets_a_permanent_password(cognito):
    provider, stubber = cognito
    stubber.add_response(
        "admin_create_user",
        _created(),
        {
            "UserPoolId": POOL,
            "Username": "a@example.test",
            "UserAttributes": [{"Name": "email", "Value": "a@example.test"}, {"Name": "name", "Value": "Ana"}],
            "MessageAction": "SUPPRESS",
        },
    )
    stubber.add_response(
        "admin_set_user_password",
        {},
        {"UserPoolId": POOL, "Username": SUB, "Password": "una-contraseña", "Permanent": True},
    )
    user = provider.create_user("a@example.test", "una-contraseña", "Ana")
    assert user.sub == SUB


def test_existing_email_maps_to_email_already_registered(cognito):
    provider, stubber = cognito
    stubber.add_client_error("admin_create_user", "UsernameExistsException")
    with pytest.raises(EmailAlreadyRegistered):
        provider.create_user("a@example.test", "una-contraseña", "Ana")


def test_rejected_password_deletes_the_half_created_account(cognito):
    provider, stubber = cognito
    stubber.add_response("admin_create_user", _created(), None)
    stubber.add_client_error("admin_set_user_password", "InvalidPasswordException", "Password does not conform")
    stubber.add_response("admin_delete_user", {}, {"UserPoolId": POOL, "Username": SUB})
    with pytest.raises(PasswordRejected):
        provider.create_user("a@example.test", "una-contraseña", "Ana")


def test_authenticate_uses_the_admin_server_side_flow(cognito):
    provider, stubber = cognito
    stubber.add_response(
        "admin_initiate_auth",
        {"AuthenticationResult": {"AccessToken": "token", "ExpiresIn": 3600, "TokenType": "Bearer"}},
        {
            "UserPoolId": POOL,
            "ClientId": CLIENT,
            "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
            "AuthParameters": {"USERNAME": "a@example.test", "PASSWORD": "una-contraseña"},
        },
    )
    token = provider.authenticate("a@example.test", "una-contraseña")
    assert (token.access_token, token.expires_in) == ("token", 3600)


@pytest.mark.parametrize("code", ["NotAuthorizedException", "UserNotFoundException", "UserNotConfirmedException"])
def test_bad_credentials_all_look_the_same(cognito, code):
    provider, stubber = cognito
    stubber.add_client_error("admin_initiate_auth", code)
    with pytest.raises(InvalidCredentials):
        provider.authenticate("a@example.test", "x")


def test_a_challenge_is_not_a_login(cognito):
    provider, stubber = cognito
    stubber.add_response("admin_initiate_auth", {"ChallengeName": "NEW_PASSWORD_REQUIRED", "Session": "s" * 20}, None)
    with pytest.raises(InvalidCredentials):
        provider.authenticate("a@example.test", "x")


def test_throttling_is_unavailable_not_a_bad_password(cognito):
    provider, stubber = cognito
    stubber.add_client_error("admin_initiate_auth", "TooManyRequestsException")
    with pytest.raises(IdentityUnavailable):
        provider.authenticate("a@example.test", "x")


def test_get_user_of_a_deleted_account_is_none(cognito):
    provider, stubber = cognito
    stubber.add_client_error("admin_get_user", "UserNotFoundException")
    assert provider.get_user(SUB) is None


def test_get_user_reads_email_and_name(cognito):
    provider, stubber = cognito
    stubber.add_response(
        "admin_get_user",
        {
            "Username": SUB,
            "Enabled": True,
            "UserAttributes": [
                {"Name": "sub", "Value": SUB},
                {"Name": "email", "Value": "a@example.test"},
                {"Name": "name", "Value": "Ana"},
            ],
        },
        {"UserPoolId": POOL, "Username": SUB},
    )
    user = provider.get_user(SUB)
    assert (user.email, user.display_name) == ("a@example.test", "Ana")


def test_deleting_a_missing_account_is_not_an_error(cognito):
    provider, stubber = cognito
    stubber.add_client_error("admin_delete_user", "UserNotFoundException")
    provider.delete_user(SUB)


def _token(**overrides):
    now = int(time.time())
    claims = {"sub": SUB, "iss": ISSUER, "client_id": CLIENT, "token_use": "access", "exp": now + 600, **overrides}
    return jwt.encode(claims, KEY, algorithm="RS256")


def test_verifies_a_cognito_shaped_access_token(cognito):
    provider, _ = cognito
    assert provider.verify_access_token(_token()) == SUB


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_OtherPool"},
        {"client_id": "other"},
        {"token_use": "id"},
        {"exp": int(time.time()) - 10},
    ],
    ids=["other-pool", "other-client", "id-token", "expired"],
)
def test_rejects_bad_cognito_tokens(cognito, overrides):
    provider, _ = cognito
    with pytest.raises(Unauthenticated):
        provider.verify_access_token(_token(**overrides))


def test_id_token_with_audience_is_rejected(cognito):
    provider, _ = cognito
    with pytest.raises(Unauthenticated):
        provider.verify_access_token(_token(aud=CLIENT, token_use="id"))


def test_rejects_a_token_signed_with_another_key(cognito):
    provider, _ = cognito
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode(
        {"sub": SUB, "iss": ISSUER, "client_id": CLIENT, "token_use": "access", "exp": int(time.time()) + 600},
        other,
        algorithm="RS256",
    )
    with pytest.raises(Unauthenticated):
        provider.verify_access_token(forged)


def test_rejects_an_unsigned_token(cognito):
    provider, _ = cognito
    unsigned = jwt.encode(
        {"sub": SUB, "iss": ISSUER, "client_id": CLIENT, "token_use": "access", "exp": int(time.time()) + 600},
        None,
        algorithm="none",
    )
    with pytest.raises(Unauthenticated):
        provider.verify_access_token(unsigned)


def test_create_user_passes_any_display_name(cognito):
    provider, stubber = cognito
    stubber.add_response("admin_create_user", _created(), {"UserPoolId": POOL, "Username": ANY,
                                                          "UserAttributes": ANY, "MessageAction": "SUPPRESS"})
    stubber.add_response("admin_set_user_password", {}, None)
    provider.create_user("a@example.test", "una-contraseña", "Ñandú Pérez")
