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


def test_test_config_never_falls_back_to_the_dev_database(monkeypatch):
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/nureon_dev")

    assert get_config("test").SQLALCHEMY_DATABASE_URI.endswith("/nureon_test")


def test_unknown_environment_name_fails():
    with pytest.raises(ConfigError):
        get_config("staging")


def test_create_app_in_production_without_required_vars_fails_naming_the_variable(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(ConfigError, match="SECRET_KEY"):
        create_app("production")


def test_subset_sizes_default_to_20_and_60(monkeypatch):
    monkeypatch.delenv("SUBSET_SIZE_FREE_REDUCED", raising=False)
    monkeypatch.delenv("SUBSET_SIZE_PAID_FULL", raising=False)
    config = get_config("test")
    assert (config.SUBSET_SIZE_FREE_REDUCED, config.SUBSET_SIZE_PAID_FULL) == (20, 60)


def test_subset_sizes_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("SUBSET_SIZE_FREE_REDUCED", "12")
    monkeypatch.setenv("SUBSET_SIZE_PAID_FULL", "40")
    config = get_config("test")
    assert (config.SUBSET_SIZE_FREE_REDUCED, config.SUBSET_SIZE_PAID_FULL) == (12, 40)


@pytest.mark.parametrize("value", ["21", "0", "-4", "veinte", "2.5"])
def test_a_subset_size_that_does_not_split_across_the_four_systems_fails(monkeypatch, value):
    monkeypatch.setenv("SUBSET_SIZE_FREE_REDUCED", value)
    with pytest.raises(ConfigError, match="SUBSET_SIZE_FREE_REDUCED"):
        get_config("test")
