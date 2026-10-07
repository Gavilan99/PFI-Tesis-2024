import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:4200")

import pytest

from app import create_app
from app.services.identity import LocalIdentityProvider
from tests.db_helpers import bound_session
from tests.migration_helpers import rebuild_schema


@pytest.fixture(scope="session")
def app():
    return create_app("test")


@pytest.fixture(scope="session")
def migrated_database(app):
    """The test database, rebuilt from the migrations once per test session."""
    rebuild_schema(app.config["SQLALCHEMY_DATABASE_URI"])
    return app.config["SQLALCHEMY_DATABASE_URI"]


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app, migrated_database):
    """A session bound to a transaction that is rolled back after each test."""
    with bound_session(app) as session:
        yield session


@pytest.fixture()
def identity(app):
    """A fresh local identity provider per test, so accounts never leak between tests."""
    original = app.extensions["identity_provider"]
    provider = LocalIdentityProvider()
    app.extensions["identity_provider"] = provider
    yield provider
    app.extensions["identity_provider"] = original


@pytest.fixture()
def api(client, db_session, identity):
    """A test client whose requests hit the rolled-back test transaction and the local identity."""
    return client
