"""Amazon Cognito user pool, reached from the backend with boto3. The browser never talks to it.

Flows, and the IAM actions they need (the app client has no secret and only
ADMIN_USER_PASSWORD_AUTH enabled):
- register: AdminCreateUser (MessageAction=SUPPRESS, no invitation mail) + AdminSetUserPassword
  (Permanent=True). The account is confirmed on creation, as decided: there is no verification screen.
- login: AdminInitiateAuth with ADMIN_USER_PASSWORD_AUTH, the server-side flow.
- provisioning fallback: AdminGetUser. Account deletion: AdminDeleteUser.
Only the access token is used. Verifying it needs no IAM: the pool's JWKS is public.
"""

import logging

import boto3
import jwt
from botocore.exceptions import BotoCoreError, ClientError

from app.exceptions import (
    EmailAlreadyRegistered,
    IdentityUnavailable,
    InvalidCredentials,
    PasswordRejected,
    ValidationFailed,
)
from app.services.identity.base import IdentityProvider, IdentityUser, IssuedToken
from app.services.identity.tokens import AccessTokenVerifier

logger = logging.getLogger(__name__)

_BAD_CREDENTIALS = ("NotAuthorizedException", "UserNotFoundException", "UserNotConfirmedException")


def _error_code(exc: Exception) -> str:
    if isinstance(exc, ClientError):
        return exc.response.get("Error", {}).get("Code", "")
    return type(exc).__name__


def _attributes(raw: list[dict]) -> dict[str, str]:
    return {item["Name"]: item["Value"] for item in raw}


def _unavailable(operation: str, exc: Exception) -> IdentityUnavailable:
    # The error code only: Cognito messages can echo request parameters back.
    logger.error("Cognito %s failed: %s", operation, _error_code(exc))
    return IdentityUnavailable()


class CognitoIdentityProvider(IdentityProvider):
    def __init__(
        self,
        region: str,
        user_pool_id: str,
        client_id: str,
        *,
        profile: str | None,
        client=None,
        jwks_client=None,
    ):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        if client is None:
            # Explicit profile from config, never boto3's implicit choice. `None` only where config
            # allows it (deployed, with role credentials and no profile file).
            if profile == "default":
                raise ValueError("The 'default' AWS profile is never used by this backend.")
            client = boto3.Session(profile_name=profile, region_name=region).client("cognito-idp")
        self._client = client
        jwks = jwks_client or jwt.PyJWKClient(f"{self.issuer}/.well-known/jwks.json", cache_keys=True)
        self._verifier = AccessTokenVerifier(
            self.issuer, client_id, lambda token: jwks.get_signing_key_from_jwt(token).key
        )

    def create_user(self, email: str, password: str, display_name: str) -> IdentityUser:
        try:
            created = self._client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "name", "Value": display_name},
                ],
                MessageAction="SUPPRESS",
            )
        except ClientError as exc:
            code = _error_code(exc)
            if code in ("UsernameExistsException", "AliasExistsException"):
                raise EmailAlreadyRegistered() from None
            if code == "InvalidParameterException":
                raise ValidationFailed() from None
            raise _unavailable("AdminCreateUser", exc) from None
        except BotoCoreError as exc:
            raise _unavailable("AdminCreateUser", exc) from None

        sub = _attributes(created["User"]["Attributes"])["sub"]
        try:
            self._client.admin_set_user_password(
                UserPoolId=self.user_pool_id, Username=sub, Password=password, Permanent=True
            )
        except (ClientError, BotoCoreError) as exc:
            # Never leave a half-created account behind: it would hold the email forever.
            self.delete_user(sub)
            if _error_code(exc) in ("InvalidPasswordException", "InvalidParameterException"):
                raise PasswordRejected() from None
            raise _unavailable("AdminSetUserPassword", exc) from None
        return IdentityUser(sub=sub, email=email, display_name=display_name)

    def authenticate(self, email: str, password: str) -> IssuedToken:
        try:
            response = self._client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password},
            )
        except ClientError as exc:
            if _error_code(exc) in _BAD_CREDENTIALS:
                raise InvalidCredentials() from None
            raise _unavailable("AdminInitiateAuth", exc) from None
        except BotoCoreError as exc:
            raise _unavailable("AdminInitiateAuth", exc) from None

        result = response.get("AuthenticationResult")
        if not result:
            # A challenge (e.g. NEW_PASSWORD_REQUIRED) means an account this backend did not finish.
            logger.warning("Cognito answered login with challenge %s", response.get("ChallengeName"))
            raise InvalidCredentials()
        return IssuedToken(result["AccessToken"], int(result["ExpiresIn"]))

    def verify_access_token(self, token: str) -> str:
        return self._verifier.verify(token)

    def get_user(self, sub: str) -> IdentityUser | None:
        try:
            response = self._client.admin_get_user(UserPoolId=self.user_pool_id, Username=sub)
        except ClientError as exc:
            if _error_code(exc) == "UserNotFoundException":
                return None
            raise _unavailable("AdminGetUser", exc) from None
        except BotoCoreError as exc:
            raise _unavailable("AdminGetUser", exc) from None
        if not response.get("Enabled", True):
            return None
        attributes = _attributes(response.get("UserAttributes", []))
        return IdentityUser(sub=attributes["sub"], email=attributes["email"], display_name=attributes.get("name"))

    def delete_user(self, sub: str) -> None:
        try:
            self._client.admin_delete_user(UserPoolId=self.user_pool_id, Username=sub)
        except ClientError as exc:
            if _error_code(exc) == "UserNotFoundException":
                return
            raise _unavailable("AdminDeleteUser", exc) from None
        except BotoCoreError as exc:
            raise _unavailable("AdminDeleteUser", exc) from None
