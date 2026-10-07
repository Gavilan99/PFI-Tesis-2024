"""Selecting the mail sender. The local double is not a production mode."""

import pytest

from app import create_app
from app.config import LOCAL_CONTACT_MAIL_TO, ConfigError, get_config
from app.services.mail import LocalMailSender, SesMailSender, build_mail_sender


@pytest.fixture()
def production_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/db")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://nureon.example")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "us-east-2_example")
    monkeypatch.setenv("COGNITO_APP_CLIENT_ID", "exampleclientid")
    monkeypatch.setenv("CLASSIFIER_BACKEND", "stub")
    monkeypatch.setenv("CONTACT_MAIL_TO", "contacto@nureon.example")
    monkeypatch.delenv("CONTACT_MAIL_FROM", raising=False)
    monkeypatch.delenv("IDENTITY_PROVIDER", raising=False)
    monkeypatch.delenv("MAIL_SENDER", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)


def test_production_defaults_to_ses_and_sends_from_the_inbox_itself(production_env):
    config = get_config("production")
    assert config.MAIL_SENDER == "ses"
    assert config.CONTACT_MAIL_FROM == config.CONTACT_MAIL_TO == "contacto@nureon.example"
    assert isinstance(build_mail_sender(config), SesMailSender)


def test_production_refuses_to_start_with_the_local_double(production_env, monkeypatch):
    monkeypatch.setenv("MAIL_SENDER", "local")
    with pytest.raises(ConfigError, match="MAIL_SENDER=local"):
        create_app("production")


def test_ses_requires_the_destination(production_env, monkeypatch):
    monkeypatch.delenv("CONTACT_MAIL_TO")
    with pytest.raises(ConfigError, match="CONTACT_MAIL_TO"):
        get_config("production")


def test_a_separate_sender_address_can_be_configured(production_env, monkeypatch):
    monkeypatch.setenv("CONTACT_MAIL_FROM", "no-responder@nureon.example")
    assert get_config("production").CONTACT_MAIL_FROM == "no-responder@nureon.example"


def test_unknown_mail_sender_fails(monkeypatch):
    monkeypatch.setenv("MAIL_SENDER", "smtp")
    with pytest.raises(ConfigError, match="MAIL_SENDER desconocido"):
        get_config("development")


def test_development_with_ses_needs_an_explicit_profile_and_never_default(monkeypatch):
    monkeypatch.setenv("IDENTITY_PROVIDER", "local")
    monkeypatch.setenv("MAIL_SENDER", "ses")
    monkeypatch.setenv("CONTACT_MAIL_TO", "contacto@nureon.example")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with pytest.raises(ConfigError, match="AWS_PROFILE"):
        get_config("development")
    monkeypatch.setenv("AWS_PROFILE", "default")
    with pytest.raises(ConfigError, match="AWS_PROFILE=default"):
        get_config("development")


def test_the_suite_never_talks_to_ses_nor_sees_a_real_inbox_whatever_the_env_says(monkeypatch):
    monkeypatch.setenv("MAIL_SENDER", "ses")
    monkeypatch.setenv("CONTACT_MAIL_TO", "casilla-real@example.com")
    monkeypatch.setenv("CONTACT_MAIL_FROM", "otra-real@example.com")
    config = get_config("test")
    assert config.MAIL_SENDER == "local"
    assert config.CONTACT_MAIL_TO == config.CONTACT_MAIL_FROM == LOCAL_CONTACT_MAIL_TO
    assert isinstance(build_mail_sender(config), LocalMailSender)


@pytest.mark.parametrize("name", ["CONTACT_RATE_LIMIT", "CONTACT_RATE_WINDOW_SECONDS"])
@pytest.mark.parametrize("value", ["0", "-3", "muchos"])
def test_the_rate_limit_must_be_a_positive_integer(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError, match=name):
        get_config("test")


def test_the_rate_limit_defaults_to_5_per_hour(monkeypatch):
    monkeypatch.delenv("CONTACT_RATE_LIMIT", raising=False)
    monkeypatch.delenv("CONTACT_RATE_WINDOW_SECONDS", raising=False)
    config = get_config("test")
    assert (config.CONTACT_RATE_LIMIT, config.CONTACT_RATE_WINDOW_SECONDS) == (5, 3600)
