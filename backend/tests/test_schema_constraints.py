"""Constraints the database enforces on its own, independent of any application code.

Each failing case asserts the exact constraint Postgres reports, so a test cannot pass because a
different constraint happened to fire.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    AnswerOption,
    ClassifierPrediction,
    Feedback,
    Payment,
    Question,
    Response,
    Result,
    Subject,
    Subscription,
    TestAttempt,
    User,
)
from app.db.models.enums import (
    AttemptStatus,
    AttemptTier,
    GroupingSystem,
    QuestionType,
    SubscriptionStatus,
    SubscriptionTier,
)

NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)


def assert_violates(session, constraint: str, *rows) -> None:
    """Flushing `rows` must fail on exactly `constraint`. The session stays usable afterwards."""
    savepoint = session.begin_nested()
    with pytest.raises(IntegrityError) as excinfo:
        session.add_all(rows)
        session.flush()
    savepoint.rollback()
    assert excinfo.value.orig.diag.constraint_name == constraint


def add(session, *rows):
    session.add_all(rows)
    session.flush()
    return rows[0] if len(rows) == 1 else rows


_counter = iter(range(1, 1_000_000))


def make_user(session, **overrides) -> User:
    n = next(_counter)
    values = {"cognito_sub": f"sub-{n}", "email": f"user{n}@example.test", "display_name": f"user{n}"}
    return add(session, User(**{**values, **overrides}))


def make_question(session, n_options: int = 3) -> Question:
    question = add(
        session,
        Question(
            grouping_system=GroupingSystem.INTELLIGENCE_CENTERS,
            question_type=QuestionType.SCENARIO,
            prompt_text="Relleno de test.",
            version=0,
            display_order=next(_counter),
        ),
    )
    groups = ("gut", "heart", "head")
    add(
        session,
        *[
            AnswerOption(
                question_id=question.id,
                option_text=f"Opción {k}",
                group_label=groups[k % 3],
                display_order=k + 1,
            )
            for k in range(n_options)
        ],
    )
    session.refresh(question)
    return question


def make_attempt(session, user: User, **overrides) -> TestAttempt:
    values = {"user_id": user.id, "tier": AttemptTier.FREE_REDUCED, "questionnaire_version": 0}
    return add(session, TestAttempt(**{**values, **overrides}))


# --- test_attempts ------------------------------------------------------------------------------


def test_attempt_with_both_user_and_subject_is_rejected(db_session):
    professional = make_user(db_session)
    subject = add(db_session, Subject(professional_user_id=professional.id, label="S"))
    user = make_user(db_session)
    assert_violates(
        db_session,
        "ck_test_attempts_user_xor_subject",
        TestAttempt(
            user_id=user.id,
            subject_id=subject.id,
            tier=AttemptTier.FREE_REDUCED,
            questionnaire_version=0,
        ),
    )


def test_attempt_with_neither_user_nor_subject_is_rejected(db_session):
    assert_violates(
        db_session,
        "ck_test_attempts_user_xor_subject",
        TestAttempt(tier=AttemptTier.FREE_REDUCED, questionnaire_version=0),
    )


def test_attempt_with_only_a_user_or_only_a_subject_is_accepted(db_session):
    user = make_user(db_session)
    subject = add(db_session, Subject(professional_user_id=make_user(db_session).id))
    make_attempt(db_session, user)
    add(
        db_session,
        TestAttempt(subject_id=subject.id, tier=AttemptTier.PAID_FULL, questionnaire_version=0),
    )


def test_attempt_check_is_enforced_by_the_database_not_the_model(db_session):
    with pytest.raises(IntegrityError) as excinfo:
        db_session.execute(
            text(
                "INSERT INTO test_attempts (tier, questionnaire_version) "
                "VALUES ('free_reduced', 0)"
            )
        )
    assert excinfo.value.orig.diag.constraint_name == "ck_test_attempts_user_xor_subject"


def test_only_one_in_progress_attempt_per_user(db_session):
    user = make_user(db_session)
    make_attempt(db_session, user)
    assert_violates(
        db_session,
        "uq_test_attempts_user_id_in_progress",
        TestAttempt(user_id=user.id, tier=AttemptTier.FREE_REDUCED, questionnaire_version=0),
    )


def test_finished_attempts_do_not_count_against_the_in_progress_limit(db_session):
    user = make_user(db_session)
    make_attempt(db_session, user, status=AttemptStatus.COMPLETED, completed_at=NOW)
    make_attempt(db_session, user, status=AttemptStatus.ABANDONED)
    make_attempt(db_session, user)


def test_completed_attempt_needs_completed_at(db_session):
    user = make_user(db_session)
    assert_violates(
        db_session,
        "ck_test_attempts_completed_at_matches_status",
        TestAttempt(
            user_id=user.id,
            tier=AttemptTier.FREE_REDUCED,
            questionnaire_version=0,
            status=AttemptStatus.COMPLETED,
        ),
    )


# --- responses ----------------------------------------------------------------------------------


def test_response_whose_option_belongs_to_another_question_is_rejected(db_session):
    question = make_question(db_session)
    other_question = make_question(db_session)
    attempt = make_attempt(db_session, make_user(db_session))
    assert_violates(
        db_session,
        "fk_responses_question_id_selected_option_id_answer_options",
        Response(
            test_attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=other_question.answer_options[0].id,
            answered_at=NOW,
            display_order=1,
        ),
    )


def test_response_with_an_option_of_its_own_question_is_accepted(db_session):
    question = make_question(db_session)
    attempt = make_attempt(db_session, make_user(db_session))
    add(
        db_session,
        Response(
            test_attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=question.answer_options[1].id,
            answered_at=NOW,
            display_order=1,
        ),
    )


def test_unanswered_response_row_is_accepted(db_session):
    question = make_question(db_session)
    attempt = make_attempt(db_session, make_user(db_session))
    add(
        db_session,
        Response(test_attempt_id=attempt.id, question_id=question.id, display_order=1),
    )


@pytest.mark.parametrize("with_option", [True, False])
def test_selected_option_and_answered_at_go_together(db_session, with_option):
    question = make_question(db_session)
    attempt = make_attempt(db_session, make_user(db_session))
    response = Response(test_attempt_id=attempt.id, question_id=question.id, display_order=1)
    if with_option:
        response.selected_option_id = question.answer_options[0].id
    else:
        response.answered_at = NOW
    assert_violates(db_session, "ck_responses_selected_option_matches_answered_at", response)


def test_one_response_per_question_within_an_attempt(db_session):
    question = make_question(db_session)
    attempt = make_attempt(db_session, make_user(db_session))
    add(db_session, Response(test_attempt_id=attempt.id, question_id=question.id, display_order=1))
    assert_violates(
        db_session,
        "uq_responses_test_attempt_id_question_id",
        Response(test_attempt_id=attempt.id, question_id=question.id, display_order=2),
    )


def test_display_order_is_unique_within_an_attempt(db_session):
    first, second = make_question(db_session), make_question(db_session)
    attempt = make_attempt(db_session, make_user(db_session))
    add(db_session, Response(test_attempt_id=attempt.id, question_id=first.id, display_order=1))
    assert_violates(
        db_session,
        "uq_responses_test_attempt_id_display_order",
        Response(test_attempt_id=attempt.id, question_id=second.id, display_order=1),
    )


# --- no cascade deletes responses ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("table", "constraint"),
    [
        ("test_attempts", "fk_responses_test_attempt_id_test_attempts"),
        ("questions", "fk_answer_options_question_id_questions"),
        ("answer_options", "fk_responses_question_id_selected_option_id_answer_options"),
    ],
)
def test_deleting_a_parent_of_responses_is_restricted(db_session, table, constraint):
    question = make_question(db_session)
    attempt = make_attempt(db_session, make_user(db_session))
    option = question.answer_options[0]
    add(
        db_session,
        Response(
            test_attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=option.id,
            answered_at=NOW,
            display_order=1,
        ),
    )
    target = {"test_attempts": attempt.id, "questions": question.id, "answer_options": option.id}[table]
    savepoint = db_session.begin_nested()
    with pytest.raises(IntegrityError) as excinfo:
        db_session.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": target})
    savepoint.rollback()
    assert excinfo.value.orig.diag.constraint_name == constraint
    assert db_session.query(Response).count() == 1


def test_deleting_a_user_with_attempts_is_restricted(db_session):
    user = make_user(db_session)
    make_attempt(db_session, user)
    savepoint = db_session.begin_nested()
    with pytest.raises(IntegrityError) as excinfo:
        db_session.execute(delete(User).where(User.id == user.id))
    savepoint.rollback()
    assert excinfo.value.orig.diag.constraint_name == "fk_test_attempts_user_id_users"


# --- users --------------------------------------------------------------------------------------


def test_cognito_sub_is_unique(db_session):
    make_user(db_session, cognito_sub="same-sub")
    assert_violates(db_session, "uq_users_cognito_sub", User(cognito_sub="same-sub", email="x@example.test"))


def test_email_is_unique_among_live_accounts(db_session):
    make_user(db_session, email="dup@example.test")
    assert_violates(
        db_session,
        "uq_users_email_not_deleted",
        User(cognito_sub="other", email="dup@example.test"),
    )


def test_deleted_accounts_do_not_hold_their_email(db_session):
    make_user(db_session, email="reused@example.test", is_deleted=True, deleted_at=NOW)
    make_user(db_session, email="reused@example.test")


def test_anonymized_accounts_do_not_collide(db_session):
    for _ in range(2):
        make_user(db_session, cognito_sub=None, email=None, display_name=None, is_deleted=True, deleted_at=NOW)


@pytest.mark.parametrize(("is_deleted", "deleted_at"), [(True, None), (False, NOW)])
def test_deleted_at_matches_is_deleted(db_session, is_deleted, deleted_at):
    assert_violates(
        db_session,
        "ck_users_deleted_at_matches_flag",
        User(cognito_sub="s", email="e@example.test", is_deleted=is_deleted, deleted_at=deleted_at),
    )


# --- predictions, results, feedback, payments, options -------------------------------------------


def test_one_prediction_per_grouping_system_within_an_attempt(db_session):
    attempt = make_attempt(db_session, make_user(db_session))

    def prediction():
        return ClassifierPrediction(
            test_attempt_id=attempt.id,
            grouping_system=GroupingSystem.HARMONIC,
            predicted_group="reactive",
            probabilities={"reactive": 1.0},
            model_version="test",
        )

    add(db_session, prediction())
    assert_violates(
        db_session, "uq_classifier_predictions_test_attempt_id_grouping_system", prediction()
    )


def test_one_result_per_attempt(db_session):
    attempt = make_attempt(db_session, make_user(db_session))
    add(db_session, Result(test_attempt_id=attempt.id, eneatype=4, description_text="x"))
    assert_violates(
        db_session,
        "uq_results_test_attempt_id",
        Result(test_attempt_id=attempt.id, eneatype=5, description_text="y"),
    )


@pytest.mark.parametrize("eneatype", [0, 10])
def test_eneatype_is_between_1_and_9(db_session, eneatype):
    attempt = make_attempt(db_session, make_user(db_session))
    assert_violates(
        db_session,
        "ck_results_eneatype_range",
        Result(test_attempt_id=attempt.id, eneatype=eneatype, description_text="x"),
    )


@pytest.mark.parametrize("rating", [0, 6])
def test_feedback_rating_is_between_1_and_5(db_session, rating):
    assert_violates(db_session, "ck_feedback_rating_range", Feedback(rating=rating))


@pytest.mark.parametrize("rating", [1, 5])
def test_feedback_rating_bounds_are_accepted(db_session, rating):
    add(db_session, Feedback(rating=rating))


def test_mercadopago_payment_id_is_unique(db_session):
    subscription = add(
        db_session,
        Subscription(
            user_id=make_user(db_session).id,
            tier=SubscriptionTier.BASIC,
            status=SubscriptionStatus.ACTIVE,
        ),
    )

    def payment():
        return Payment(
            subscription_id=subscription.id,
            mercadopago_payment_id="mp-123",
            amount=100,
            currency="ARS",
            status="approved",
        )

    add(db_session, payment())
    assert_violates(db_session, "uq_payments_mercadopago_payment_id", payment())


def test_group_label_outside_the_canonical_vocabulary_is_rejected(db_session):
    question = make_question(db_session, n_options=0)
    assert_violates(
        db_session,
        "ck_answer_options_group_label_canonical",
        AnswerOption(question_id=question.id, option_text="x", group_label="Cuerpo", display_order=1),
    )


def test_enum_rejects_values_outside_the_vocabulary(db_session):
    savepoint = db_session.begin_nested()
    with pytest.raises(Exception) as excinfo:
        db_session.execute(
            text(
                "INSERT INTO questions (grouping_system, question_type, prompt_text, version, display_order) "
                "VALUES ('centros', 'scenario', 'x', 0, 1)"
            )
        )
    savepoint.rollback()
    assert "invalid input value for enum grouping_system" in str(excinfo.value)


def test_ids_and_timestamps_are_generated_by_the_database(db_session):
    row = db_session.execute(
        text(
            "INSERT INTO users (cognito_sub, email) VALUES ('db-gen', 'dbgen@example.test') "
            "RETURNING id, created_at, is_deleted"
        )
    ).one()
    assert row.id is not None
    assert row.created_at.tzinfo is not None
    assert row.is_deleted is False
