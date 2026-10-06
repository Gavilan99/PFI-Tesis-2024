import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:4200")

import pytest

from app import create_app
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
