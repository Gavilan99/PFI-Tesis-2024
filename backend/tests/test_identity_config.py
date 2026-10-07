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
    monkeypatch.delenv("AWS_PROFILE", raising=False)


@pytest.fixture()
def development_cognito_env(monkeypatch):
    monkeypatch.setenv("IDENTITY_PROVIDER", "cognito")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "sa-east-1_example")
    monkeypatch.setenv("COGNITO_APP_CLIENT_ID", "exampleclientid")
    monkeypatch.setenv("AWS_PROFILE", "nureon")


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


# --- AWS profile: explicit, from config, never `default` -----------------------------------------


class _RecordingSession:
    calls: list[dict] = []

    def __init__(self, **kwargs):
        _RecordingSession.calls.append(kwargs)

    def client(self, service_name):
        return object()


@pytest.fixture()
def recorded_sessions(monkeypatch):
    from app.services.identity import cognito

    _RecordingSession.calls = []
    monkeypatch.setattr(cognito.boto3, "Session", _RecordingSession)
    return _RecordingSession.calls


def test_boto3_gets_the_configured_profile_explicitly(development_cognito_env, recorded_sessions):
    provider = build_identity_provider(get_config("development"))

    assert isinstance(provider, CognitoIdentityProvider)
    assert recorded_sessions == [{"profile_name": "nureon", "region_name": "sa-east-1"}]


def test_cognito_outside_production_requires_aws_profile(development_cognito_env, monkeypatch):
    monkeypatch.delenv("AWS_PROFILE")
    with pytest.raises(ConfigError, match="AWS_PROFILE"):
        get_config("development")


@pytest.mark.parametrize("env_name", ["development", "production"])
def test_the_default_profile_is_refused(development_cognito_env, production_env, monkeypatch, env_name):
    monkeypatch.setenv("IDENTITY_PROVIDER", "cognito")
    monkeypatch.setenv("AWS_PROFILE", "default")
    with pytest.raises(ConfigError, match="AWS_PROFILE=default"):
        get_config(env_name)


def test_provider_refuses_the_default_profile_even_if_config_is_bypassed(recorded_sessions):
    with pytest.raises(ValueError):
        CognitoIdentityProvider("sa-east-1", "sa-east-1_x", "client", profile="default")
    assert recorded_sessions == []


def test_production_without_a_profile_uses_the_platform_role(production_env, recorded_sessions):
    build_identity_provider(get_config("production"))
    assert recorded_sessions == [{"profile_name": None, "region_name": "sa-east-1"}]
