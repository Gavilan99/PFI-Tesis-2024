import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app.db.models import AnswerOption, Question, Response, TestAttempt, User
from app.db.models.enums import AttemptStatus, AttemptTier


def lock_user(session: Session, user_id: uuid.UUID) -> None:
    """Serializes attempt creation per user: two concurrent "start" requests would otherwise both
    abandon the old attempt and both insert a new one, and the second would hit the unique index."""
    session.execute(select(User.id).where(User.id == user_id).with_for_update())


def abandon_in_progress(session: Session, user_id: uuid.UUID) -> None:
    session.execute(
        update(TestAttempt)
        .where(TestAttempt.user_id == user_id, TestAttempt.status == AttemptStatus.IN_PROGRESS)
        .values(status=AttemptStatus.ABANDONED)
    )


def current_version(session: Session) -> int | None:
    """The highest version with active questions. One active version at a time is what the import
    script guarantees, not the database, so this picks one and everything after filters by it."""
    return session.scalar(select(func.max(Question.version)).where(Question.is_active))


def active_questions(session: Session, version: int) -> list[Row]:
    return list(
        session.execute(
            select(Question.id, Question.grouping_system, Question.question_type).where(
                Question.version == version, Question.is_active
            )
        )
    )


def option_ids_in_bank_order(
    session: Session, question_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[uuid.UUID]]:
    rows = session.execute(
        select(AnswerOption.question_id, AnswerOption.id)
        .where(AnswerOption.question_id.in_(question_ids))
        .order_by(AnswerOption.question_id, AnswerOption.display_order)
    )
    options: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for question_id, option_id in rows:
        options[question_id].append(option_id)
    return options


def insert_attempt(session: Session, *, user_id: uuid.UUID, tier: AttemptTier, version: int) -> TestAttempt:
    attempt = TestAttempt(
        user_id=user_id,
        tier=tier,
        questionnaire_version=version,
        # The column default is now(), the transaction's start time. clock_timestamp() is the moment
        # of the insert, so attempts created close together still sort newest first.
        started_at=func.clock_timestamp(),
    )
    session.add(attempt)
    session.flush()
    session.refresh(attempt)
    return attempt


def insert_served_items(
    session: Session, attempt_id: uuid.UUID, items: list[tuple[uuid.UUID, list[uuid.UUID]]]
) -> None:
    """One unanswered row per (question id, option order), in serving order."""
    session.add_all(
        Response(
            test_attempt_id=attempt_id, question_id=question_id, display_order=position, option_order=order
        )
        for position, (question_id, order) in enumerate(items, start=1)
    )
    session.flush()


def get_owned(
    session: Session, attempt_id: uuid.UUID, user_id: uuid.UUID, *, for_update: bool = False
) -> TestAttempt | None:
    query = select(TestAttempt).where(TestAttempt.id == attempt_id, TestAttempt.user_id == user_id)
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


def latest_for_user(session: Session, user_id: uuid.UUID) -> TestAttempt | None:
    return session.scalar(
        select(TestAttempt)
        .where(TestAttempt.user_id == user_id)
        .order_by(TestAttempt.started_at.desc(), TestAttempt.id.desc())
        .limit(1)
    )


def history_for_user(session: Session, user_id: uuid.UUID) -> list[TestAttempt]:
    return list(
        session.scalars(
            select(TestAttempt)
            .where(TestAttempt.user_id == user_id)
            .order_by(TestAttempt.started_at.desc(), TestAttempt.id.desc())
        )
    )


def served_questions(session: Session, attempt_id: uuid.UUID) -> list[Row]:
    """The attempt's items in serving order, with only the columns the client may see."""
    return list(
        session.execute(
            select(
                Question.id,
                Question.question_type,
                Question.prompt_text,
                Response.display_order,
                Response.option_order,
            )
            .join(Question, Question.id == Response.question_id)
            .where(Response.test_attempt_id == attempt_id)
            .order_by(Response.display_order)
        )
    )


def option_texts(session: Session, question_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    """Option id -> text. `group_label` is not selected: it never reaches the code that serializes."""
    if not question_ids:
        return {}
    rows = session.execute(
        select(AnswerOption.id, AnswerOption.option_text).where(AnswerOption.question_id.in_(question_ids))
    )
    return {option_id: text for option_id, text in rows}


def get_response(
    session: Session, attempt_id: uuid.UUID, question_id: uuid.UUID, *, for_update: bool = False
) -> Response | None:
    query = select(Response).where(
        Response.test_attempt_id == attempt_id, Response.question_id == question_id
    )
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


def record_answer(session: Session, response: Response, option_id: uuid.UUID, now: datetime) -> Response:
    response.selected_option_id = option_id
    response.answered_at = now
    session.flush()
    return response


def answered_responses(session: Session, attempt_id: uuid.UUID) -> list[Response]:
    return list(
        session.scalars(
            select(Response)
            .where(Response.test_attempt_id == attempt_id, Response.selected_option_id.is_not(None))
            .order_by(Response.display_order)
        )
    )


def unanswered_count(session: Session, attempt_id: uuid.UUID) -> int:
    return session.scalar(
        select(func.count())
        .select_from(Response)
        .where(Response.test_attempt_id == attempt_id, Response.selected_option_id.is_(None))
    )


def mark_completed(session: Session, attempt: TestAttempt) -> TestAttempt:
    attempt.status = AttemptStatus.COMPLETED
    attempt.completed_at = func.clock_timestamp()
    session.flush()
    session.refresh(attempt)
    return attempt
