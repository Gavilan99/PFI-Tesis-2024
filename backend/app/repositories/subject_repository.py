import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app.db.models import Subject, TestAttempt


def find_active_by_label(
    session: Session, professional_user_id: uuid.UUID, label: str, *, for_update: bool = False
) -> Subject | None:
    """The professional's own active subject with this label, case-insensitively, if any.

    `for_update` locks the row (Feature 20): `_resolve_subject` takes it so that reusing a subject
    to administer a new attempt can't race with `delete_subject` anonymizing the very same row —
    whichever of the two gets there first finishes before the other proceeds, instead of both
    reading the row as still active and leaving a live attempt pointing at an anonymized subject.
    """
    query = select(Subject).where(
        Subject.professional_user_id == professional_user_id,
        func.lower(Subject.label) == label.lower(),
        Subject.deleted_at.is_(None),
    )
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


def insert(session: Session, *, professional_user_id: uuid.UUID, label: str, consent_at: datetime) -> Subject:
    """flush() alone is enough: `id` and `created_at` come back via RETURNING, no refresh needed."""
    subject = Subject(professional_user_id=professional_user_id, label=label, consent_declared_at=consent_at)
    session.add(subject)
    session.flush()
    return subject


def touch_consent(session: Session, subject: Subject, now: datetime) -> None:
    """The declaration is per test: overwritten every time, new subject or not."""
    subject.consent_declared_at = now
    session.flush()


def get_active_owned(
    session: Session, subject_id: uuid.UUID, professional_user_id: uuid.UUID, *, for_update: bool = False
) -> Subject | None:
    """`for_update` locks the row: `delete_subject` takes it for the same reason `find_active_by_label`
    does — serialized against a concurrent attempt that would otherwise reuse this very subject."""
    query = select(Subject).where(
        Subject.id == subject_id,
        Subject.professional_user_id == professional_user_id,
        Subject.deleted_at.is_(None),
    )
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


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
    new attempt's context). Ordered by that newest attempt, subjects without one last.

    The count and the newest row are both window functions over the same partition, computed in
    one pass over `test_attempts` instead of two separate subqueries. The join to `Subject` here,
    inside the windowed subquery, narrows that pass to this professional's own subjects before the
    aggregation runs, instead of windowing over every account's subject-linked attempts first and
    only filtering down to this one afterwards.
    """
    ranked = (
        select(
            TestAttempt.subject_id,
            TestAttempt.started_at,
            TestAttempt.subject_context,
            func.count().over(partition_by=TestAttempt.subject_id).label("test_count"),
            func.row_number()
            .over(partition_by=TestAttempt.subject_id, order_by=TestAttempt.started_at.desc())
            .label("rank"),
        )
        .join(Subject, Subject.id == TestAttempt.subject_id)
        .where(TestAttempt.subject_id.is_not(None), Subject.professional_user_id == professional_user_id)
        .subquery()
    )
    latest = (
        select(ranked.c.subject_id, ranked.c.started_at, ranked.c.subject_context, ranked.c.test_count)
        .where(ranked.c.rank == 1)
        .subquery()
    )

    return list(
        session.execute(
            select(
                Subject.id,
                Subject.label,
                func.coalesce(latest.c.test_count, 0).label("test_count"),
                latest.c.started_at.label("last_test_at"),
                latest.c.subject_context.label("last_test_context"),
            )
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
