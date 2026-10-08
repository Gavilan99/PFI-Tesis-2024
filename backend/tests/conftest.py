import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:4200")
# Not setdefault: a developer's shell or .env choosing legacy_tree must not change what the suite
# runs. Tests that need another backend build their own app (tests/classifier_helpers.py).
os.environ["CLASSIFIER_BACKEND"] = "stub"

import pytest

from app import create_app
from app.services.identity import LocalIdentityProvider
from app.services.mail import LocalMailSender
from app.services.rate_limit import SlidingWindowLimiter
from tests import leak_guard
from tests.db_helpers import bound_session
from tests.migration_helpers import rebuild_schema


def pytest_configure(config):
    # Every JSON response of the whole suite goes through the answer-key guard. Not optional, and not
    # per endpoint: see tests/leak_guard.py.
    leak_guard.install()


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line(
        f"Answer-key guard: {leak_guard.stats.json_responses} JSON responses checked."
    )


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
def mailbox(app):
    """A fresh local mail sender per test: what the contact form would have sent, nothing sent."""
    original = app.extensions["mail_sender"]
    sender = LocalMailSender()
    app.extensions["mail_sender"] = sender
    yield sender
    app.extensions["mail_sender"] = original


@pytest.fixture()
def contact_limiter(app):
    """A fresh contact rate limiter per test, with the configured limit, so counts never carry over."""
    original = app.extensions["contact_rate_limiter"]
    limiter = SlidingWindowLimiter(app.config["CONTACT_RATE_LIMIT"], app.config["CONTACT_RATE_WINDOW_SECONDS"])
    app.extensions["contact_rate_limiter"] = limiter
    yield limiter
    app.extensions["contact_rate_limiter"] = original


@pytest.fixture()
def api(client, db_session, identity, mailbox, contact_limiter):
    """A test client whose requests hit the rolled-back test transaction, the local identity and the
    local mail sender."""
    return client


@pytest.fixture()
def question_bank(db_session):
    """The filler bank, version 0, loaded and active inside the test transaction."""
    from app.services.question_bank import load_bank
    from scripts.seed_filler_bank import FILLER_VERSION, build_filler_bank

    load_bank(db_session, build_filler_bank(), version=FILLER_VERSION, activate=True)
    db_session.commit()
    return FILLER_VERSION
