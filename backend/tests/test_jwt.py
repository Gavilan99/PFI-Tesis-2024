"""Every protected route verifies an access token: signature, issuer, client, expiration, token type.

The identity comes from the token and from nowhere else.
"""

import pytest
from sqlalchemy import select

from app.db.models import User
from app.services.identity import LocalIdentityProvider
from tests.auth_helpers import assert_error, bearer, registered

PROTECTED = [("get", "/api/users/me"), ("patch", "/api/users/me"), ("delete", "/api/users/me")]


def _sub(db_session, user) -> str:
    return db_session.get(User, user["id"]).cognito_sub


def _call(client, method, path, headers=None):
    return getattr(client, method)(path, headers=headers or {}, json={} if method == "patch" else None)


@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_missing_token_is_401(api, method, path):
    assert_error(_call(api, method, path), 401, "UNAUTHORIZED")


def test_expired_token_is_401(api, identity, db_session):
    user, _ = registered(api)
    token = identity.mint_access_token(_sub(db_session, user), lifetime=-60)
    assert_error(api.get("/api/users/me", headers=bearer(token)), 401, "UNAUTHORIZED")


def test_token_with_invalid_signature_is_401(api, db_session):
    user, _ = registered(api)
    # Same issuer and client, signed with another key.
    forger = LocalIdentityProvider()
    token = forger.mint_access_token(_sub(db_session, user))
    assert_error(api.get("/api/users/me", headers=bearer(token)), 401, "UNAUTHORIZED")


def test_token_with_tampered_payload_is_401(api, identity, db_session):
    user, headers = registered(api)
    header, payload, signature = headers["Authorization"].removeprefix("Bearer ").split(".")
    tampered = ".".join([header, payload[:-2] + ("AA" if payload[-2:] != "AA" else "BB"), signature])
    assert_error(api.get("/api/users/me", headers=bearer(tampered)), 401, "UNAUTHORIZED")


def test_token_from_another_pool_is_401(api, db_session):
    user, _ = registered(api)
    other_pool = LocalIdentityProvider(pool_id="another-pool")
    token = other_pool.mint_access_token(_sub(db_session, user))
    assert_error(api.get("/api/users/me", headers=bearer(token)), 401, "UNAUTHORIZED")


def test_token_with_another_issuer_but_a_valid_signature_is_401(api, identity, db_session):
    user, _ = registered(api)
    token = identity.mint_access_token(_sub(db_session, user), issuer="https://local-identity.invalid/another-pool")
    assert_error(api.get("/api/users/me", headers=bearer(token)), 401, "UNAUTHORIZED")


def test_token_for_another_client_is_401(api, identity, db_session):
    user, _ = registered(api)
    token = identity.mint_access_token(_sub(db_session, user), client_id="another-client")
    assert_error(api.get("/api/users/me", headers=bearer(token)), 401, "UNAUTHORIZED")


def test_id_token_is_not_accepted_as_an_access_token(api, identity, db_session):
    user, _ = registered(api)
    token = identity.mint_access_token(_sub(db_session, user), token_use="id")
    assert_error(api.get("/api/users/me", headers=bearer(token)), 401, "UNAUTHORIZED")


@pytest.mark.parametrize("header", ["", "Bearer", "Bearer ", "Basic abc", "Token abc", "Bearer not.a.jwt"])
def test_malformed_authorization_header_is_401(api, header):
    assert_error(api.get("/api/users/me", headers={"Authorization": header}), 401, "UNAUTHORIZED")


def test_token_of_an_unknown_account_is_401(api, identity):
    token = identity.mint_access_token("00000000-0000-0000-0000-000000000000")
    assert_error(api.get("/api/users/me", headers=bearer(token)), 401, "UNAUTHORIZED")


def test_client_supplied_identity_headers_are_ignored(api, db_session):
    alice, alice_headers = registered(api, username="Alice")
    bob, _ = registered(api, username="Bob")

    response = api.get(
        "/api/users/me",
        headers={**alice_headers, "userType": "rrhh", "X-User-Id": bob["id"], "userId": bob["id"]},
    )

    assert response.get_json()["id"] == alice["id"]
    assert response.get_json()["accountType"] is None


def test_public_routes_need_no_token(api):
    assert api.get("/api/health").status_code == 200


def test_every_route_except_the_public_ones_requires_a_token(app):
    public = {
        "core.health", "core.health_ready", "auth.register", "auth.login", "feedback.submit_contact_message",
    }
    for rule in app.url_map.iter_rules():
        view = app.view_functions[rule.endpoint]
        is_public = getattr(view, "_public_endpoint", False)
        assert is_public == (rule.endpoint in public), rule.endpoint


def test_first_authenticated_request_provisions_a_missing_row(api, identity, db_session):
    account = identity.create_user("solo-cognito@example.test", "una-contraseña", "Solo Cognito")
    token = identity.mint_access_token(account.sub)

    response = api.get("/api/users/me", headers=bearer(token))

    assert response.status_code == 200
    assert response.get_json()["email"] == "solo-cognito@example.test"
    assert response.get_json()["displayName"] == "Solo Cognito"
    rows = db_session.scalars(select(User).where(User.cognito_sub == account.sub)).all()
    assert len(rows) == 1
