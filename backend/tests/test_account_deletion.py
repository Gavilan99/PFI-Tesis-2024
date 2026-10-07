"""DELETE /api/users/me: soft delete with anonymization (Ley 25.326, "Borrado de cuenta" in CLAUDE.md).

Nothing is deleted physically. What identifies the person is nulled; what serves the dataset stays.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.db.models import (
    ClassifierPrediction,
    Feedback,
    Payment,
    Response,
    Result,
    Subject,
    Subscription,
    TestAttempt,
    User,
)
from app.db.models.enums import AttemptStatus, GroupingSystem, SubscriptionStatus, SubscriptionTier
from app.exceptions import IdentityUnavailable
from tests.auth_helpers import PASSWORD, assert_error, register, registered
from tests.db_helpers import option_ids
from tests.test_schema_constraints import add, make_attempt, make_question

NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)
USER_COLUMNS = (
    "email", "display_name", "cognito_sub", "account_type", "age_range", "gender", "country",
    "profession_context", "is_deleted", "deleted_at",
)

KEPT_TABLES = (User, TestAttempt, Response, ClassifierPrediction, Result, Feedback, Subject, Subscription, Payment)


def _snapshot(row: User) -> dict:
    return {column: getattr(row, column) for column in USER_COLUMNS}


@pytest.fixture()
def account(api, db_session):
    """A registered account with a full profile and something in every table deletion touches."""
    user, headers = registered(api, username="Juana Identificable")
    api.patch(
        "/api/users/me",
        headers=headers,
        json={
            "accountType": "salud",
            "ageRange": "25-34",
            "gender": "femenino",
            "country": "Argentina",
            "professionContext": "Psicóloga en el Hospital X",
        },
    )
    row = db_session.get(User, user["id"])
    db_session.refresh(row)

    question = make_question(db_session)
    attempt = make_attempt(db_session, row, status=AttemptStatus.COMPLETED, completed_at=NOW)
    add(
        db_session,
        Response(
            test_attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=question.answer_options[0].id,
            answered_at=NOW,
            display_order=1,
            option_order=option_ids(question),
        ),
        ClassifierPrediction(
            test_attempt_id=attempt.id,
            grouping_system=GroupingSystem.INTELLIGENCE_CENTERS,
            predicted_group="gut",
            probabilities={"gut": 1.0},
            model_version="stub",
        ),
        Result(test_attempt_id=attempt.id, eneatype=8, description_text="Provisorio."),
        Feedback(test_attempt_id=attempt.id, user_id=row.id, rating=4, comment="Me reconocí, soy Juana."),
        # Feedback tied only to the attempt, without user_id: still hers.
        Feedback(test_attempt_id=attempt.id, rating=5, comment="Firmado: Juana."),
        Subject(professional_user_id=row.id, label="Paciente Pérez", context_data={"dni": "12345678"}),
    )
    subscription = add(
        db_session,
        Subscription(user_id=row.id, tier=SubscriptionTier.BASIC, status=SubscriptionStatus.ACTIVE),
    )
    add(
        db_session,
        Payment(
            subscription_id=subscription.id,
            mercadopago_payment_id=f"mp-{row.id}",
            amount=Decimal("1000.00"),
            currency="ARS",
            status="approved",
        ),
    )
    db_session.commit()
    return {"user": user, "headers": headers, "row": row, "attempt": attempt}


def _count(session, model, *where) -> int:
    return session.scalar(select(func.count()).select_from(model).where(*where))


def test_deletion_anonymizes_exactly_what_the_table_says(api, identity, db_session, account):
    row, attempt = account["row"], account["attempt"]
    sub = row.cognito_sub
    before = _snapshot(row)
    counts_before = {model: _count(db_session, model) for model in KEPT_TABLES}

    response = api.delete("/api/users/me", headers=account["headers"])

    assert response.status_code == 204
    db_session.expire_all()
    after = _snapshot(db_session.get(User, row.id))
    print("\nusers row before:", before)
    print("users row after: ", after)

    # Nulled.
    assert after["email"] is None
    assert after["display_name"] is None
    assert after["cognito_sub"] is None
    assert after["profession_context"] is None
    # Kept: demographics and account type.
    for column in ("account_type", "age_range", "gender", "country"):
        assert after[column] == before[column] is not None, column
    assert after["is_deleted"] is True
    assert after["deleted_at"] is not None

    # Nothing deleted physically, anywhere.
    assert {model: _count(db_session, model) for model in KEPT_TABLES} == counts_before

    # The attempt and its answers survive, still linked to the (now anonymous) row.
    assert db_session.get(TestAttempt, attempt.id).user_id == row.id
    answered = db_session.scalars(select(Response).where(Response.test_attempt_id == attempt.id)).all()
    assert len(answered) == 1 and answered[0].selected_option_id is not None
    assert db_session.scalar(select(Result.eneatype).where(Result.test_attempt_id == attempt.id)) == 8
    assert _count(db_session, ClassifierPrediction, ClassifierPrediction.test_attempt_id == attempt.id) == 1

    # Feedback: comment nulled, rating kept.
    feedback = db_session.scalars(select(Feedback).where(Feedback.test_attempt_id == attempt.id)).all()
    assert sorted(f.rating for f in feedback) == [4, 5]
    assert all(f.comment is None for f in feedback)

    # Subjects: label and context nulled, the row stays.
    subject = db_session.scalar(select(Subject).where(Subject.professional_user_id == row.id))
    assert subject.label is None and subject.context_data is None

    # Billing kept.
    assert _count(db_session, Subscription, Subscription.user_id == row.id) == 1
    assert _count(db_session, Payment) == counts_before[Payment]

    # And the account is gone from the identity provider.
    assert identity.get_user(sub) is None


def test_old_token_stops_working_after_deletion(api, account):
    assert api.delete("/api/users/me", headers=account["headers"]).status_code == 204
    for method in ("get", "patch", "delete"):
        response = getattr(api, method)("/api/users/me", headers=account["headers"], json={} if method == "patch" else None)
        assert_error(response, 401, "UNAUTHORIZED")


def test_deleted_account_cannot_log_in(api, account):
    api.delete("/api/users/me", headers=account["headers"])
    response = api.post("/api/auth/login", json={"email": account["user"]["email"], "password": PASSWORD})
    assert_error(response, 401, "INVALID_CREDENTIALS", "Email o contraseña incorrectos.")


def test_same_email_can_register_again_after_deletion(api, db_session, account):
    email = account["user"]["email"]
    api.delete("/api/users/me", headers=account["headers"])

    response = register(api, email=email, username="Cuenta nueva")

    assert response.status_code == 201
    new_user = response.get_json()["user"]
    assert new_user["id"] != account["user"]["id"]
    assert new_user["accountType"] is None
    assert _count(db_session, User, User.email == email) == 1


def test_other_accounts_are_untouched(api, db_session, account):
    other, other_headers = registered(api, username="Otra persona")
    api.patch("/api/users/me", headers=other_headers, json={"professionContext": "RRHH"})

    api.delete("/api/users/me", headers=account["headers"])

    assert api.get("/api/users/me", headers=other_headers).get_json()["professionContext"] == "RRHH"


def test_provider_failure_rolls_the_deletion_back(api, identity, db_session, account, monkeypatch):
    def unavailable(sub):
        raise IdentityUnavailable()

    monkeypatch.setattr(identity, "delete_user", unavailable)

    response = api.delete("/api/users/me", headers=account["headers"])

    assert_error(response, 503, "IDENTITY_UNAVAILABLE")
    db_session.expire_all()
    row = db_session.get(User, account["row"].id)
    assert row.is_deleted is False
    assert row.email == account["user"]["email"]
    assert db_session.scalar(select(Feedback.comment).where(Feedback.user_id == row.id)) is not None
    assert api.get("/api/users/me", headers=account["headers"]).status_code == 200
