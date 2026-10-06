import pytest

from app import create_app
from app.config import ConfigError, get_config


def test_production_requires_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/db")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://nureon.example")

    with pytest.raises(ConfigError, match="SECRET_KEY"):
        get_config("production")


def test_production_requires_database_url(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://nureon.example")

    with pytest.raises(ConfigError, match="DATABASE_URL"):
        get_config("production")


def test_production_requires_cors_allowed_origins(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/db")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(ConfigError, match="CORS_ALLOWED_ORIGINS"):
        get_config("production")


def test_unknown_environment_name_fails():
    with pytest.raises(ConfigError):
        get_config("staging")


def test_create_app_in_production_without_required_vars_fails_naming_the_variable(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(ConfigError, match="SECRET_KEY"):
        create_app("production")
