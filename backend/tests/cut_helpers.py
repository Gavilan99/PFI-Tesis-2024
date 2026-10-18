"""Helpers for the fixed item cuts: the paid tier, the real bank, and walking an attempt through cuts."""

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.db.models.enums import SubscriptionTier
from app.repositories import subscription_repository
from app.services.question_bank import load_bank
from scripts.import_question_bank import read_bank_csv
from tests.attempt_helpers import answer_all, questions

REAL_BANK_CSV = Path(__file__).resolve().parents[2] / "research" / "bank" / "NureonAI Prototype v4.1.2.csv"
REAL_BANK_VERSION = 1


def give_paid_tier(session, user_id, *, days: int = 30, end: datetime | None = None) -> None:
    """An active subscription, as scripts/grant_subscription.py writes it."""
    start = datetime.now(timezone.utc)
    subscription_repository.insert_manual(
        session,
        uuid.UUID(str(user_id)),
        tier=SubscriptionTier.INDIVIDUAL,
        start=start,
        end=end if end is not None else start + timedelta(days=days),
    )
    session.commit()


def load_real_bank(session) -> int:
    """Bank v4.1.2 as version 1, active: what the trained models were trained on."""
    load_bank(session, read_bank_csv(REAL_BANK_CSV), version=REAL_BANK_VERSION, activate=True)
    session.commit()
    return REAL_BANK_VERSION


def answer_everything(client, headers, attempt_id: str) -> list[dict]:
    items = questions(client, headers, attempt_id)
    answer_all(client, headers, attempt_id, [q for q in items])
    return items


def continue_(client, headers, attempt_id: str):
    return client.post(f"/api/attempts/{attempt_id}/continue", headers=headers)


def cut(client, headers, attempt_id: str) -> dict:
    response = client.get(f"/api/attempts/{attempt_id}/cut", headers=headers)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def complete(client, headers, attempt_id: str) -> dict:
    response = client.post(f"/api/attempts/{attempt_id}/complete", headers=headers)
    assert response.status_code == 200, response.get_json()
    return response.get_json()
