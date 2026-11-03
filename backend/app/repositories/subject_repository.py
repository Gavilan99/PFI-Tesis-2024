import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app.db.models import Subject, TestAttempt


def find_active_by_label(session: Session, professional_user_id: uuid.UUID, label: str) -> Subject | None:
    """The professional's own active subject with this label, case-insensitively, if any."""
    return session.scalar(
        select(Subject).where(
            Subject.professional_user_id == professional_user_id,
            func.lower(Subject.label) == label.lower(),
            Subject.deleted_at.is_(None),
        )
    )


def insert(session: Session, *, professional_user_id: uuid.UUID, label: str, consent_at: datetime) -> Subject:
    subject = Subject(professional_user_id=professional_user_id, label=label, consent_declared_at=consent_at)
    session.add(subject)
    session.flush()
    session.refresh(subject)
    return subject


def touch_consent(session: Session, subject: Subject, now: datetime) -> None:
    """The declaration is per test: overwritten every time, new subject or not."""
    subject.consent_declared_at = now
    session.flush()


def get_active_owned(session: Session, subject_id: uuid.UUID, professional_user_id: uuid.UUID) -> Subject | None:
    return session.scalar(
        select(Subject).where(
            Subject.id == subject_id,
            Subject.professional_user_id == professional_user_id,
            Subject.deleted_at.is_(None),
        )
    )


def has_active_subjects(session: Session, professional_user_id: uuid.UUID) -> bool:
    return bool(
        session.scalar(
            select(Subject.id)
            .where(Subject.professional_user_id == professional_user_id, Subject.deleted_at.is_(None))
            .limit(1)
        )
    )


def list_active_with_stats(session: Session, professional_user_id: uuid.UUID) -> list[Row]:
    """The account's active subjects with id, label, how many attempts they have, and the started
    time and declared context of the newest one (for GET /api/subjects: list, and precompleting a
    new attempt's context). Ordered by that newest attempt, subjects without one last."""
    counts = (
        select(TestAttempt.subject_id, func.count().label("test_count"))
        .where(TestAttempt.subject_id.is_not(None))
        .group_by(TestAttempt.subject_id)
        .subquery()
    )
    ranked = (
        select(
            TestAttempt.subject_id,
            TestAttempt.started_at,
            TestAttempt.subject_context,
            func.row_number()
            .over(partition_by=TestAttempt.subject_id, order_by=TestAttempt.started_at.desc())
            .label("rank"),
        )
        .where(TestAttempt.subject_id.is_not(None))
        .subquery()
    )
    latest = select(ranked.c.subject_id, ranked.c.started_at, ranked.c.subject_context).where(ranked.c.rank == 1).subquery()

    return list(
        session.execute(
            select(
                Subject.id,
                Subject.label,
                func.coalesce(counts.c.test_count, 0).label("test_count"),
                latest.c.started_at.label("last_test_at"),
                latest.c.subject_context.label("last_test_context"),
            )
            .outerjoin(counts, counts.c.subject_id == Subject.id)
            .outerjoin(latest, latest.c.subject_id == Subject.id)
            .where(Subject.professional_user_id == professional_user_id, Subject.deleted_at.is_(None))
            .order_by(latest.c.started_at.desc().nullslast(), func.lower(Subject.label))
        )
    )


def anonymize(session: Session, subject: Subject, now: datetime) -> None:
    """DELETE /api/subjects/<id>: nulls the label and the stored context, like account deletion
    already does, and frees the label for reuse. The subject's attempts, answers and results are
    kept; only their declared `subject_context` is nulled along with it."""
    subject.label = None
    subject.context_data = None
    subject.deleted_at = now
    session.execute(update(TestAttempt).where(TestAttempt.subject_id == subject.id).values(subject_context=None))
    session.flush()
