"""Selecting the identity provider. The local double is not a production mode."""

import pytest

from app import create_app
from app.config import ConfigError, get_config
from app.services.identity import CognitoIdentityProvider, LocalIdentityProvider, build_identity_provider


@pytest.fixture()
def production_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/db")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://nureon.example")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "sa-east-1_example")
    monkeypatch.setenv("COGNITO_APP_CLIENT_ID", "exampleclientid")
    monkeypatch.delenv("IDENTITY_PROVIDER", raising=False)


def test_production_refuses_to_start_with_the_local_double(production_env, monkeypatch):
    monkeypatch.setenv("IDENTITY_PROVIDER", "local")
    with pytest.raises(ConfigError, match="IDENTITY_PROVIDER=local"):
        create_app("production")


def test_production_defaults_to_cognito(production_env):
    config = get_config("production")
    assert config.IDENTITY_PROVIDER == "cognito"
    assert isinstance(build_identity_provider(config), CognitoIdentityProvider)


@pytest.mark.parametrize("missing", ["COGNITO_USER_POOL_ID", "COGNITO_APP_CLIENT_ID"])
def test_cognito_requires_its_ids(production_env, monkeypatch, missing):
    monkeypatch.delenv(missing)
    with pytest.raises(ConfigError, match=missing):
        get_config("production")


def test_unknown_identity_provider_fails(production_env, monkeypatch):
    monkeypatch.setenv("IDENTITY_PROVIDER", "firebase")
    with pytest.raises(ConfigError, match="IDENTITY_PROVIDER"):
        get_config("development")


def test_development_defaults_to_the_local_double(monkeypatch):
    monkeypatch.delenv("IDENTITY_PROVIDER", raising=False)
    assert get_config("development").IDENTITY_PROVIDER == "local"


def test_the_suite_always_uses_the_local_double(monkeypatch):
    monkeypatch.setenv("IDENTITY_PROVIDER", "cognito")
    assert get_config("test").IDENTITY_PROVIDER == "local"


def test_test_app_runs_on_the_local_double(app):
    assert isinstance(app.extensions["identity_provider"], LocalIdentityProvider)
