"""POST /api/auth/register and /api/auth/login (RF01, RF02, CU001, CU002)."""

import pytest
from sqlalchemy import select

from app.db.models import User
from tests.auth_helpers import (
    PASSWORD,
    USER_FIELDS,
    assert_error,
    bearer,
    register,
    registered,
    unique_email,
)

DUPLICATE = "Ese email ya está registrado."
BAD_CREDENTIALS = "Email o contraseña incorrectos."


def test_register_returns_the_user_and_the_access_token(api, db_session):
    email = unique_email()
    response = register(api, email=email, username="Juan Pérez")

    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == {"user", "accessToken", "expiresIn"}
    assert set(body["user"]) == USER_FIELDS
    assert body["user"]["displayName"] == "Juan Pérez"
    assert body["user"]["email"] == email
    assert body["user"]["accountType"] is None
    assert isinstance(body["expiresIn"], int) and body["expiresIn"] > 0

    row = db_session.scalar(select(User).where(User.email == email))
    assert str(row.id) == body["user"]["id"]
    assert row.cognito_sub


def test_registered_account_exists_in_the_identity_provider(api, identity, db_session):
    user, _ = registered(api)
    row = db_session.get(User, user["id"])
    assert identity.get_user(row.cognito_sub).email == user["email"]


def test_register_token_authenticates_the_new_user(api):
    user, headers = registered(api)
    response = api.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["id"] == user["id"]


def test_register_lowercases_the_email(api):
    user, _ = registered(api, email="Juan.Perez-X1@Example.TEST")
    assert user["email"] == "juan.perez-x1@example.test"


def test_duplicate_email_is_rejected_with_the_form_message(api):
    email = unique_email()
    registered(api, email=email)
    assert_error(register(api, email=email), 409, "EMAIL_ALREADY_REGISTERED", DUPLICATE)


def test_email_differing_only_in_case_is_the_same_account(api):
    registered(api, email="juan-case@x.com")
    assert_error(register(api, email="Juan-Case@X.com"), 409, "EMAIL_ALREADY_REGISTERED", DUPLICATE)


@pytest.mark.parametrize(
    "body",
    [
        {"email": "a@example.test", "password": PASSWORD},
        {"username": "abc", "password": PASSWORD},
        {"username": "abc", "email": "a@example.test"},
        {"username": "abc", "email": "a@example.test", "password": PASSWORD, "accountType": "salud"},
        {"username": "ab", "email": "a@example.test", "password": PASSWORD},
        {"username": "abc", "email": "not-an-email", "password": PASSWORD},
        {"username": "abc", "email": "a@example.test", "password": "short"},
        {"username": "abc", "email": "a@example.test", "password": 12345678},
    ],
    ids=["no-username", "no-email", "no-password", "extra-field", "short-username", "bad-email",
         "short-password", "non-string-password"],
)
def test_register_body_is_exactly_register_input(api, body):
    assert_error(api.post("/api/auth/register", json=body), 400, "VALIDATION_ERROR")


def test_register_without_json_body_is_rejected(api):
    assert_error(api.post("/api/auth/register", data="x", content_type="text/plain"), 400, "VALIDATION_ERROR")


def test_login_returns_the_same_user_and_a_token(api):
    email = unique_email()
    user, _ = registered(api, email=email)

    response = api.post("/api/auth/login", json={"email": email, "password": PASSWORD})

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"user", "accessToken", "expiresIn"}
    assert body["user"] == user
    assert api.get("/api/users/me", headers=bearer(body["accessToken"])).status_code == 200


def test_login_email_is_case_insensitive(api):
    user, _ = registered(api, email="login-case@example.test")
    response = api.post("/api/auth/login", json={"email": "LOGIN-Case@Example.test", "password": PASSWORD})
    assert response.status_code == 200
    assert response.get_json()["user"]["id"] == user["id"]


def test_wrong_password_is_rejected_with_the_form_message(api):
    email = unique_email()
    registered(api, email=email)
    response = api.post("/api/auth/login", json={"email": email, "password": "otra-contraseña"})
    assert_error(response, 401, "INVALID_CREDENTIALS", BAD_CREDENTIALS)


def test_unknown_email_looks_like_a_wrong_password(api):
    response = api.post("/api/auth/login", json={"email": unique_email(), "password": PASSWORD})
    assert_error(response, 401, "INVALID_CREDENTIALS", BAD_CREDENTIALS)


@pytest.mark.parametrize(
    "body",
    [{"email": "a@example.test"}, {"password": PASSWORD}, {"email": "a@example.test", "password": PASSWORD, "x": 1}],
    ids=["no-password", "no-email", "extra-field"],
)
def test_login_body_is_exactly_login_input(api, body):
    assert_error(api.post("/api/auth/login", json=body), 400, "VALIDATION_ERROR")


def test_failed_provisioning_does_not_leave_the_account_in_the_provider(api, identity, db_session, monkeypatch):
    from app.exceptions import AccountConflict
    from app.services import accounts

    def conflict(*args, **kwargs):
        raise AccountConflict()

    monkeypatch.setattr(accounts, "_provision", conflict)
    email = unique_email()

    assert_error(register(api, email=email), 409, "ACCOUNT_CONFLICT")
    assert identity._sub_by_email == {}
