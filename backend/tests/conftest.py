import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:4200")

import pytest
from sqlalchemy import event

from app import create_app
from app.extensions import Session


@pytest.fixture(scope="session")
def app():
    return create_app("test")


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """A session bound to a transaction that is rolled back after each test."""
    engine = app.extensions["sqlalchemy_engine"]
    connection = engine.connect()
    transaction = connection.begin()

    Session.configure(bind=connection)
    session = Session()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", _restart_savepoint)
        session.close()
        transaction.rollback()
        connection.close()
        Session.remove()
