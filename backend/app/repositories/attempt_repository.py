import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy import func, insert, literal, select, update
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


def active_question_ids_by_order(session: Session, version: int, orders: list[int]) -> dict[int, uuid.UUID]:
    """`questions.display_order` -> id, among the active questions of `version`. The display order is
    the number of the bank code (`Q007` -> 7), so this is how a cut's codes become questions."""
    rows = session.execute(
        select(Question.display_order, Question.id).where(
            Question.version == version, Question.is_active, Question.display_order.in_(orders)
        )
    )
    return {order: question_id for order, question_id in rows}


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


def insert_attempt(
    session: Session,
    *,
    user_id: uuid.UUID,
    tier: AttemptTier,
    version: int,
    continued_from: uuid.UUID | None = None,
) -> TestAttempt:
    attempt = TestAttempt(
        user_id=user_id,
        tier=tier,
        questionnaire_version=version,
        continued_from_attempt_id=continued_from,
        # The column default is now(), the transaction's start time. clock_timestamp() is the moment
        # of the insert, so attempts created close together still sort newest first.
        started_at=func.clock_timestamp(),
    )
    session.add(attempt)
    session.flush()
    session.refresh(attempt)
    return attempt


def insert_served_items(
    session: Session, attempt_id: uuid.UUID, items: list[tuple[uuid.UUID, list[uuid.UUID]]], *, first: int = 1
) -> None:
    """One unanswered row per (question id, option order), in serving order, numbered from `first`."""
    session.add_all(
        Response(
            test_attempt_id=attempt_id, question_id=question_id, display_order=position, option_order=order
        )
        for position, (question_id, order) in enumerate(items, start=first)
    )
    session.flush()


def copy_responses(session: Session, source_id: uuid.UUID, target_id: uuid.UUID) -> None:
    """Every row of `source` into `target`, as it is: question, chosen option, option order, display
    order and answered time. The source rows are not touched."""
    session.execute(
        insert(Response).from_select(
            ["test_attempt_id", "question_id", "selected_option_id", "answered_at", "display_order", "option_order"],
            select(
                literal(target_id, type_=Response.__table__.c.test_attempt_id.type),
                Response.question_id,
                Response.selected_option_id,
                Response.answered_at,
                Response.display_order,
                Response.option_order,
            ).where(Response.test_attempt_id == source_id),
        )
    )
    session.flush()


def set_tier(session: Session, attempt: TestAttempt, tier: AttemptTier) -> None:
    attempt.tier = tier
    session.flush()


def continuation_of(session: Session, attempt_id: uuid.UUID) -> uuid.UUID | None:
    """The attempt that continued this one, if any."""
    return session.scalar(select(TestAttempt.id).where(TestAttempt.continued_from_attempt_id == attempt_id))


def latest_completed_for_user(session: Session, user_id: uuid.UUID) -> uuid.UUID | None:
    return session.scalar(
        select(TestAttempt.id)
        .where(TestAttempt.user_id == user_id, TestAttempt.status == AttemptStatus.COMPLETED)
        .order_by(TestAttempt.completed_at.desc(), TestAttempt.id.desc())
        .limit(1)
    )


def served_and_answered(session: Session, attempt_id: uuid.UUID) -> tuple[int, int]:
    served, answered = session.execute(
        select(func.count(), func.count(Response.selected_option_id)).where(Response.test_attempt_id == attempt_id)
    ).one()
    return served, answered


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
