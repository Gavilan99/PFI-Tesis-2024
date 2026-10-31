import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AnswerOption, ClassifierPrediction, Question, Response, Result, TestAttempt
from app.db.models.enums import AttemptStatus, AttemptTier, GroupingSystem
from app.ml.classification import Answer, Classification
from app.repositories.attempt_repository import option_ids_in_bank_order


def classification_inputs(session: Session, attempt_id: uuid.UUID) -> list[Answer]:
    """The attempt's answers with their answer key resolved. This `group_label` goes to the
    classifier, never to a response."""
    rows = session.execute(
        select(
            Response.question_id,
            Response.selected_option_id,
            Question.grouping_system,
            Question.question_type,
            Question.display_order,
            AnswerOption.group_label,
        )
        .join(Question, Question.id == Response.question_id)
        .join(AnswerOption, AnswerOption.id == Response.selected_option_id)
        .where(Response.test_attempt_id == attempt_id)
        .order_by(Response.display_order)
    ).all()
    bank_order = option_ids_in_bank_order(session, [row.question_id for row in rows])
    return [
        Answer(
            question_id=row.question_id,
            option_id=row.selected_option_id,
            grouping_system=row.grouping_system.value,
            question_type=row.question_type,
            group_label=row.group_label,
            option_position=bank_order[row.question_id].index(row.selected_option_id) + 1,
            option_count=len(bank_order[row.question_id]),
            question_order=row.display_order,
        )
        for row in rows
    ]


def insert_classification(
    session: Session, attempt_id: uuid.UUID, classification: Classification, description_text: str
) -> Result:
    """The four raw predictions and the result, in the caller's transaction."""
    session.add_all(
        ClassifierPrediction(
            test_attempt_id=attempt_id,
            grouping_system=GroupingSystem(prediction.grouping_system),
            predicted_group=prediction.predicted_group,
            probabilities=prediction.probabilities,
            model_version=classification.model_version,
        )
        for prediction in classification.systems.values()
    )
    result = Result(
        test_attempt_id=attempt_id,
        eneatype=classification.eneatype,
        confidence_margin=Decimal(repr(classification.confidence_margin)),
        description_text=description_text,
        # Like `completed_at`: the moment of the insert, not the transaction's start, so a result is
        # never dated before the close that produced it.
        generated_at=func.clock_timestamp(),
    )
    session.add(result)
    session.flush()
    session.refresh(result)
    return result


def result_of_owned_completed_with_tier(
    session: Session, attempt_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[Result, AttemptTier] | None:
    """The user's own completed attempt's result, with the attempt's tier: GET .../result/personalized
    (Feature 17) needs the tier to tell a free attempt from a paid one. `result_of_owned_completed`
    is this same lookup minus the tier, for GET .../result, which doesn't need it."""
    row = session.execute(
        select(Result, TestAttempt.tier)
        .join(TestAttempt, TestAttempt.id == Result.test_attempt_id)
        .where(
            Result.test_attempt_id == attempt_id,
            TestAttempt.user_id == user_id,
            TestAttempt.status == AttemptStatus.COMPLETED,
        )
    ).first()
    if row is None:
        return None
    result, tier = row
    return result, tier


def result_of_owned_completed(session: Session, attempt_id: uuid.UUID, user_id: uuid.UUID) -> Result | None:
    found = result_of_owned_completed_with_tier(session, attempt_id, user_id)
    return found[0] if found else None


def lock_for_personalization(session: Session, result_id: uuid.UUID) -> None:
    """Serializes personalized-description generation for one result (Feature 17): without this,
    two concurrent requests that both see a missing or stale personalized description would each
    call the generator and each bill Bedrock for the same regeneration."""
    session.execute(select(Result.id).where(Result.id == result_id).with_for_update())


def save_personalized(
    session: Session,
    result: Result,
    *,
    strengths: list[str],
    tensions: list[str],
    growth: str,
    stress: str,
    profile_hash: str,
    model: str,
) -> None:
    """Attaches a freshly generated personalized description to `result` (Feature 17), in the
    caller's transaction. The caller commits."""
    result.personalized_strengths = strengths
    result.personalized_tensions = tensions
    result.personalized_growth = growth
    result.personalized_stress = stress
    result.personalized_profile_hash = profile_hash
    result.personalized_model = model
    result.personalized_at = func.clock_timestamp()
    session.flush()
