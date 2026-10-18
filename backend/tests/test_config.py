import pytest
from sqlalchemy.engine import make_url

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


def test_the_subset_sizes_are_gone_from_the_configuration():
    # Feature 9: the cuts (40 / 90 / 145) come from the artifacts' manifest, not from configuration.
    config = get_config("test")
    assert not any(name.startswith("SUBSET_SIZE") for name in vars(config))


# --- production database URL and proxy hops (Feature 8) ----------------------------------------

DB_PARTS = {"DB_HOST": "nureon.abc.us-east-2.rds.amazonaws.com", "DB_NAME": "nureon",
            "DB_USER": "nureon_admin", "DB_PASSWORD": "p@ss:w/rd%?#"}


def _production_env(monkeypatch, **database):
    for name, value in {
        "SECRET_KEY": "x",
        "CORS_ALLOWED_ORIGINS": "https://d111111abcdef8.cloudfront.net",
        "CLASSIFIER_BACKEND": "stub",
        "IDENTITY_PROVIDER": "cognito",
        "COGNITO_USER_POOL_ID": "us-east-2_example",
        "COGNITO_APP_CLIENT_ID": "example",
        "MAIL_SENDER": "ses",
        "CONTACT_MAIL_TO": "contacto@example.test",
    }.items():
        monkeypatch.setenv(name, value)
    for name in ("DATABASE_URL", "DB_PORT", "DB_SSLMODE", "TRUSTED_PROXY_HOPS", *DB_PARTS):
        monkeypatch.delenv(name, raising=False)
    for name, value in database.items():
        monkeypatch.setenv(name, value)


def test_production_builds_the_database_url_from_its_parts_escaping_the_password(monkeypatch):
    _production_env(monkeypatch, **DB_PARTS)

    url = make_url(get_config("production").SQLALCHEMY_DATABASE_URI)

    assert url.drivername == "postgresql+psycopg"
    assert (url.host, url.port, url.database) == (DB_PARTS["DB_HOST"], 5432, "nureon")
    assert (url.username, url.password) == ("nureon_admin", "p@ss:w/rd%?#")
    assert url.query == {"sslmode": "require"}


def test_production_prefers_a_whole_database_url(monkeypatch):
    _production_env(monkeypatch, DATABASE_URL="postgresql+psycopg://u:p@host/db", **DB_PARTS)

    assert get_config("production").SQLALCHEMY_DATABASE_URI == "postgresql+psycopg://u:p@host/db"


def test_production_names_the_missing_database_parts(monkeypatch):
    _production_env(monkeypatch, DB_HOST="host", DB_NAME="nureon")

    with pytest.raises(ConfigError, match="faltan: DB_USER, DB_PASSWORD"):
        get_config("production")


def test_production_port_and_sslmode_come_from_the_environment(monkeypatch):
    _production_env(monkeypatch, DB_PORT="5433", DB_SSLMODE="disable", **DB_PARTS)

    url = make_url(get_config("production").SQLALCHEMY_DATABASE_URI)

    assert (url.port, url.query) == (5433, {"sslmode": "disable"})


def test_production_trusts_exactly_one_proxy_hop_and_local_runs_none(monkeypatch):
    _production_env(monkeypatch, **DB_PARTS)
    assert get_config("production").TRUSTED_PROXY_HOPS == 1
    monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    assert get_config("test").TRUSTED_PROXY_HOPS == 0


@pytest.mark.parametrize("value", ["-1", "uno"])
def test_a_bad_proxy_hop_count_fails(monkeypatch, value):
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", value)
    with pytest.raises(ConfigError, match="TRUSTED_PROXY_HOPS"):
        get_config("test")
