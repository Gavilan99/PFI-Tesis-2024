"""The `users` row is tied to `cognito_sub`, and two concurrent first requests cannot create two rows.

These tests commit for real (concurrency needs separate transactions), so they clean up after
themselves instead of relying on the rolled-back fixture.
"""

import threading

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError

from app.db.models import User
from app.db.session import Session
from app.services import accounts


@pytest.fixture()
def committed(app, migrated_database, identity):
    created_subs: list[str] = []
    yield created_subs
    engine = app.extensions["sqlalchemy_engine"]
    with engine.begin() as connection:
        connection.execute(delete(User).where(User.cognito_sub.in_(created_subs)))


def test_concurrent_first_requests_create_one_row(app, identity, committed):
    account = identity.create_user("carrera@example.test", "una-contraseña", "Carrera")
    committed.append(account.sub)
    workers = 8
    barrier = threading.Barrier(workers)
    results, errors = [], []

    def first_request():
        with app.app_context():
            try:
                barrier.wait()
                results.append(accounts.authenticated_user(identity, account.sub).id)
            except Exception as exc:  # noqa: BLE001  (collected and asserted below)
                errors.append(exc)
            finally:
                Session.remove()

    threads = [threading.Thread(target=first_request) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(set(results)) == 1
    engine = app.extensions["sqlalchemy_engine"]
    with engine.connect() as connection:
        rows = connection.scalar(select(func.count()).select_from(User).where(User.cognito_sub == account.sub))
    assert rows == 1


def test_email_is_stored_lowercase_by_the_database_too(db_session):
    savepoint = db_session.begin_nested()
    with pytest.raises(IntegrityError) as excinfo:
        db_session.execute(text("INSERT INTO users (cognito_sub, email) VALUES ('s-upper', 'Upper@Example.test')"))
    savepoint.rollback()
    assert excinfo.value.orig.diag.constraint_name == "ck_users_email_is_lowercase"


def test_live_email_index_compares_lowercase(db_session):
    definition = db_session.scalar(
        text("SELECT indexdef FROM pg_indexes WHERE indexname = 'uq_users_email_not_deleted'")
    )
    assert "lower((email)::text)" in definition
    assert "WHERE (NOT is_deleted)" in definition


def test_provisioning_refuses_an_email_held_by_another_live_account(api, identity, db_session):
    db_session.add(User(cognito_sub="otra-cuenta", email="ocupado@example.test", display_name="Otra"))
    db_session.commit()
    account = identity.create_user("ocupado@example.test", "una-contraseña", "Huérfana")

    from app.exceptions import AccountConflict

    with pytest.raises(AccountConflict):
        accounts.authenticated_user(identity, account.sub)
