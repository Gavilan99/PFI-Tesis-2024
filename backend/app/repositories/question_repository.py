import uuid
from collections import Counter

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, selectinload

from app.db.models import AnswerOption, Question, Response


def questions_for_version(session: Session, version: int) -> list[Question]:
    return list(
        session.scalars(
            select(Question)
            .where(Question.version == version)
            .options(selectinload(Question.answer_options))
            .order_by(Question.display_order)
        )
    )


def version_has_responses(session: Session, version: int) -> bool:
    """Any response row counts, answered or not: a question served to an attempt is in use."""
    return session.scalar(
        select(
            select(Response.id)
            .join(Question, Question.id == Response.question_id)
            .where(Question.version == version)
            .exists()
        )
    )


def delete_options(session: Session, question_ids: list[uuid.UUID]) -> None:
    if question_ids:
        session.execute(delete(AnswerOption).where(AnswerOption.question_id.in_(question_ids)))


def delete_questions(session: Session, question_ids: list[uuid.UUID]) -> None:
    if question_ids:
        session.execute(delete(Question).where(Question.id.in_(question_ids)))


def active_versions(session: Session) -> list[int]:
    return list(
        session.scalars(
            select(Question.version).where(Question.is_active).distinct().order_by(Question.version)
        )
    )


def activate_version(session: Session, version: int) -> None:
    """Activate `version` and deactivate every other one, in a single statement."""
    session.execute(update(Question).values(is_active=Question.version == version))


def version_counts(session: Session, version: int) -> dict:
    questions = session.execute(
        select(Question.grouping_system, Question.question_type, func.count())
        .where(Question.version == version)
        .group_by(Question.grouping_system, Question.question_type)
    ).all()
    options = session.execute(
        select(Question.grouping_system, AnswerOption.group_label, func.count())
        .join(AnswerOption, AnswerOption.question_id == Question.id)
        .where(Question.version == version)
        .group_by(Question.grouping_system, AnswerOption.group_label)
    ).all()

    by_system: Counter = Counter()
    by_type: Counter = Counter()
    for system, question_type, count in questions:
        by_system[system.value] += count
        by_type[question_type.value] += count
    options_by_group = {(system.value, group): count for system, group, count in options}
    return {
        "questions": sum(by_system.values()),
        "questions_by_system": dict(by_system),
        "questions_by_type": dict(by_type),
        "options": sum(options_by_group.values()),
        "options_by_group": options_by_group,
    }
