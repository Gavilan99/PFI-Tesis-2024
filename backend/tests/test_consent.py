"""Consent to the processing of personal data (Feature 11; Ley 25.326 arts. 5, 6 and 12, decreto 1558/2001).

Registration requires `consentAccepted: true`. The server records when and which version of the texts
was in force (`CONSENT_VERSION`); the client never chooses the version. Accounts from before the
migration keep both columns in NULL. Deletion keeps both (see test_account_deletion.py).
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.config import LOCAL_CONSENT_VERSION, ConfigError, get_config
from app.db.models import User
from app.exceptions import InvalidCredentials
from tests.auth_helpers import PASSWORD, assert_error, bearer, register_body
from tests.migration_helpers import alembic_config, scratch_database
from tests.production_env import set_payment_env

CONSENT_REQUIRED = "Para crear tu cuenta tenés que aceptar la Política de privacidad y los Términos y condiciones."


def _post(api, body):
    return api.post("/api/auth/register", json=body)


def _without_consent(**overrides) -> dict:
    body = register_body(**overrides)
    del body["consentAccepted"]
    return body


@pytest.mark.parametrize("consent", ["missing", False], ids=["missing", "false"])
def test_registration_without_consent_is_rejected_in_spanish(api, identity, db_session, consent):
    body = _without_consent() if consent == "missing" else {**register_body(), "consentAccepted": False}

    assert_error(_post(api, body), 400, "CONSENT_REQUIRED", CONSENT_REQUIRED)

    # Nothing was created, neither here nor in the identity provider.
    assert db_session.scalar(select(User).where(User.email == body["email"])) is None
    with pytest.raises(InvalidCredentials):
        identity.authenticate(body["email"], PASSWORD)


@pytest.mark.parametrize("consent", ["true", 1, None, "sí"])
def test_consent_must_be_a_json_boolean(api, consent):
    assert_error(_post(api, {**register_body(), "consentAccepted": consent}), 400, "VALIDATION_ERROR")


def test_the_client_cannot_choose_the_version(api):
    body = {**register_body(), "consentVersion": "2020-01-01"}
    assert_error(_post(api, body), 400, "VALIDATION_ERROR")


def test_an_invalid_body_is_a_validation_error_even_without_consent(api):
    # The consent message is for a body that is otherwise fine: a broken one gets the generic error.
    assert_error(_post(api, _without_consent(username="ab")), 400, "VALIDATION_ERROR")


def test_registration_records_the_date_and_the_version_in_force(api, db_session):
    before = datetime.now(timezone.utc)
    response = _post(api, register_body())
    after = datetime.now(timezone.utc)

    assert response.status_code == 201, response.get_json()
    row = db_session.get(User, response.get_json()["user"]["id"])
    assert before <= row.consent_accepted_at <= after
    assert row.consent_version == LOCAL_CONSENT_VERSION


def test_the_stored_version_comes_from_configuration(app, api, db_session, monkeypatch):
    monkeypatch.setitem(app.config, "CONSENT_VERSION", "2026-10-20")

    response = _post(api, register_body())

    assert response.status_code == 201, response.get_json()
    assert db_session.get(User, response.get_json()["user"]["id"]).consent_version == "2026-10-20"


def test_the_consent_does_not_reach_the_browser(api):
    body = _post(api, register_body()).get_json()
    assert not any("consent" in key.lower() for key in body["user"])


def test_the_consent_is_recorded_whole_or_not_at_all(db_session):
    db_session.add(User(cognito_sub="sub-a-medias", email="a-medias@example.test", consent_version="2026-10-20"))
    with pytest.raises(IntegrityError, match="ck_users_consent_recorded_whole"):
        db_session.flush()


# --- configuration --------------------------------------------------------------------------------


def test_development_reads_the_version_and_falls_back_to_local(monkeypatch):
    monkeypatch.delenv("CONSENT_VERSION", raising=False)
    assert get_config("development").CONSENT_VERSION == LOCAL_CONSENT_VERSION
    monkeypatch.setenv("CONSENT_VERSION", " 2026-10-20 ")
    assert get_config("development").CONSENT_VERSION == "2026-10-20"


def test_the_suite_always_records_the_local_version(monkeypatch):
    monkeypatch.setenv("CONSENT_VERSION", "2026-10-20")
    assert get_config("test").CONSENT_VERSION == LOCAL_CONSENT_VERSION


def _production_env(monkeypatch):
    for name, value in {
        "SECRET_KEY": "x", "DATABASE_URL": "postgresql+psycopg://u:p@host/db",
        "CORS_ALLOWED_ORIGINS": "https://nureon.example", "CLASSIFIER_BACKEND": "stub",
        "IDENTITY_PROVIDER": "cognito", "COGNITO_USER_POOL_ID": "us-east-2_pool", "COGNITO_APP_CLIENT_ID": "client",
        "MAIL_SENDER": "ses", "CONTACT_MAIL_TO": "contacto@example.invalid",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    set_payment_env(monkeypatch)


def test_production_requires_choosing_the_version(monkeypatch):
    _production_env(monkeypatch)
    monkeypatch.delenv("CONSENT_VERSION", raising=False)
    with pytest.raises(ConfigError, match="CONSENT_VERSION"):
        get_config("production")

    monkeypatch.setenv("CONSENT_VERSION", "2026-10-20")
    assert get_config("production").CONSENT_VERSION == "2026-10-20"


def test_a_version_longer_than_the_column_fails(monkeypatch):
    monkeypatch.setenv("CONSENT_VERSION", "x" * 33)
    with pytest.raises(ConfigError, match="CONSENT_VERSION puede tener hasta 32 caracteres"):
        get_config("development")


# --- migration 0005 -------------------------------------------------------------------------------


def test_existing_accounts_keep_no_consent_through_the_migration(app):
    with scratch_database(app.config["SQLALCHEMY_DATABASE_URI"]) as url:
        config = alembic_config(url)
        command.upgrade(config, "0004")
        engine = create_engine(url)
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO users (cognito_sub, email) VALUES ('sub-previa', 'previa@example.test')")
            )

        command.upgrade(config, "0005")
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT consent_accepted_at, consent_version FROM users WHERE cognito_sub = 'sub-previa'")
            ).one()
        assert tuple(row) == (None, None)

        command.downgrade(config, "0004")
        with engine.connect() as connection:
            columns = connection.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
            ).scalars().all()
        assert not any(column.startswith("consent") for column in columns)
        engine.dispose()


# --- one version everywhere -----------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[2]
VERSION_SOURCES = {
    "frontend/nureon/src/app/legal/legal-content.ts": r"LEGAL_TEXT_VERSION = '([^']+)'",
    "backend/.env.example": r"^CONSENT_VERSION=(\S+)$",
    "backend/docker-compose.prod.yml": r'CONSENT_VERSION: "([^"]+)"',
    "backend/infra/09-service.ps1": r"\$ConsentVersion = '([^']+)'",
}


def test_the_version_shown_is_the_version_stored():
    # The pages show LEGAL_TEXT_VERSION; the deployment stores CONSENT_VERSION. A text that changes in
    # one place only would record that people accepted a version they never saw.
    found = {}
    for path, pattern in VERSION_SOURCES.items():
        match = re.search(pattern, (REPO / path).read_text(encoding="utf-8-sig"), re.MULTILINE)
        assert match, f"no version found in {path}"
        found[path] = match.group(1)
    assert len(set(found.values())) == 1, found


# --- the fallback provisioning: an account in the provider that never registered here --------------

NOT_ENABLED = "Esta cuenta no está habilitada en NureonAI. Registrate con otro email."


def _provider_only_account(identity):
    """An account in the identity provider with no `users` row, like a development account in the
    shared Cognito pool trying production."""
    return identity.create_user("solo-proveedor@example.test", PASSWORD, "Solo proveedor")


def test_outside_production_the_fallback_still_provisions_on_login(api, identity, db_session):
    account = _provider_only_account(identity)

    response = api.post("/api/auth/login", json={"email": "solo-proveedor@example.test", "password": PASSWORD})

    assert response.status_code == 200, response.get_json()
    row = db_session.scalar(select(User).where(User.cognito_sub == account.sub))
    assert row is not None and row.consent_accepted_at is None


def test_production_refuses_the_login_without_creating_the_row(app, api, identity, db_session, monkeypatch):
    monkeypatch.setitem(app.config, "PROVISION_MISSING_ACCOUNTS", False)
    account = _provider_only_account(identity)

    response = api.post("/api/auth/login", json={"email": "solo-proveedor@example.test", "password": PASSWORD})

    assert_error(response, 401, "ACCOUNT_NOT_ENABLED", NOT_ENABLED)
    assert db_session.scalar(select(User).where(User.cognito_sub == account.sub)) is None
    # The provider account is left alone: the pool is shared with development.
    assert identity.get_user(account.sub) is not None


def test_production_refuses_an_authenticated_request_too(app, api, identity, db_session, monkeypatch):
    monkeypatch.setitem(app.config, "PROVISION_MISSING_ACCOUNTS", False)
    account = _provider_only_account(identity)

    response = api.get("/api/users/me", headers=bearer(identity.mint_access_token(account.sub)))

    assert_error(response, 401, "ACCOUNT_NOT_ENABLED", NOT_ENABLED)
    assert db_session.scalar(select(User).where(User.cognito_sub == account.sub)) is None


def test_production_still_lets_registered_accounts_in(app, api, monkeypatch):
    monkeypatch.setitem(app.config, "PROVISION_MISSING_ACCOUNTS", False)
    body = register_body()
    assert _post(api, body).status_code == 201

    response = api.post("/api/auth/login", json={"email": body["email"], "password": PASSWORD})

    assert response.status_code == 200, response.get_json()


def test_only_production_turns_the_fallback_off(monkeypatch):
    assert get_config("development").PROVISION_MISSING_ACCOUNTS is True
    assert get_config("test").PROVISION_MISSING_ACCOUNTS is True
    _production_env(monkeypatch)
    monkeypatch.setenv("CONSENT_VERSION", "2026-10-20")
    monkeypatch.setenv("PROVISION_MISSING_ACCOUNTS", "true")  # not a setting: nothing turns it back on
    assert get_config("production").PROVISION_MISSING_ACCOUNTS is False
