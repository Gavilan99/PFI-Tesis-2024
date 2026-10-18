"""scripts/grant_subscription.py: a manual paid tier, with no payment behind it, said out loud."""

import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.db.models import Payment, Subscription
from app.services import tiers
from scripts import grant_subscription
from tests.auth_helpers import registered


@pytest.fixture()
def run(db_session, monkeypatch):
    """The script against the rolled-back test transaction."""

    @contextmanager
    def same_session(url):
        yield db_session
        # As the real one does when it closes: what the script still holds must not need the session.
        db_session.expunge_all()

    monkeypatch.setattr(grant_subscription, "open_session", same_session)
    monkeypatch.setattr(grant_subscription, "database_url", lambda: "postgresql+psycopg://u:p@localhost:5433/nureon_test")
    return grant_subscription.main


def test_it_grants_the_paid_tier_for_n_days_and_says_it_is_manual(api, run, db_session, capsys):
    user, _ = registered(api, email="Pago.Manual@example.com")
    assert not tiers.has_paid_tier(db_session, uuid.UUID(user["id"]))

    assert run(["--email", "pago.manual@EXAMPLE.com", "--days", "14"]) == 0
    out = capsys.readouterr().out
    assert "ALTA MANUAL" in out and "SIN PAGO ASOCIADO" in out
    assert user["id"] in out
    assert "pago.manual" not in out.lower()  # the output goes to CloudWatch in production: no email

    subscription = db_session.scalar(select(Subscription))
    assert subscription.user_id == uuid.UUID(user["id"])
    assert (subscription.tier.value, subscription.status.value) == ("individual", "active")
    assert subscription.mercadopago_subscription_id is None
    assert abs(subscription.current_period_end - datetime.now(timezone.utc) - timedelta(days=14)) < timedelta(minutes=1)
    assert db_session.scalar(select(Payment.id)) is None
    assert tiers.has_paid_tier(db_session, uuid.UUID(user["id"]))


def test_an_unknown_email_grants_nothing(api, run, db_session, capsys):
    assert run(["--email", "nadie@example.com", "--days", "3"]) == 1
    assert "no se dio de alta nada" in capsys.readouterr().err
    assert db_session.scalar(select(Subscription.id)) is None


@pytest.mark.parametrize("days", ["0", "-1", "400"])
def test_the_days_are_bounded(api, run, db_session, days):
    registered(api, email="dias@example.com")
    assert run(["--email", "dias@example.com", "--days", days]) == 2
    assert db_session.scalar(select(Subscription.id)) is None


def test_dry_run_saves_nothing(api, run, db_session, capsys):
    registered(api, email="simulacion@example.com")
    assert run(["--email", "simulacion@example.com", "--days", "5", "--dry-run"]) == 0
    assert "SIMULACIÓN" in capsys.readouterr().out
    db_session.expire_all()
    assert db_session.scalar(select(Subscription.id)) is None
