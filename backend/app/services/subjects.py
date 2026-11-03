"""Evaluados (Feature 20): the people a salud/rrhh account tests in person, from its own account.

A subject belongs to exactly one account (`professional_user_id`) and is never shared or listed
across accounts. Every route here is refused outright, with `SubjectsNotAllowed` (403), for any
account whose `account_type` isn't salud or rrhh — including for a subject that would otherwise be
someone else's, so the 403 says nothing about whether it exists.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import User
from app.db.models.enums import AccountType
from app.db.session import Session
from app.exceptions import SubjectNotFound, SubjectsNotAllowed
from app.repositories import subject_repository


@dataclass(frozen=True)
class SubjectSummary:
    """A row of GET /api/subjects: enough to list the account's evaluados and precomplete a new
    attempt's context from the last one's."""

    id: uuid.UUID
    label: str
    test_count: int
    last_test_at: datetime | None
    last_test_context: str | None


def require_professional(user: User) -> None:
    """The one place the "salud or rrhh" rule lives: shared with `app.services.attempts`, which
    needs the same check for `CreateAttemptIn.subject`."""
    if user.account_type not in (AccountType.SALUD, AccountType.RRHH):
        raise SubjectsNotAllowed()


def list_subjects(user: User) -> list[SubjectSummary]:
    require_professional(user)
    rows = subject_repository.list_active_with_stats(Session(), user.id)
    return [
        SubjectSummary(
            id=row.id,
            label=row.label,
            test_count=row.test_count,
            last_test_at=row.last_test_at,
            last_test_context=row.last_test_context,
        )
        for row in rows
    ]


def delete_subject(user: User, subject_id: uuid.UUID) -> None:
    """Anonymizes the subject (label and context_data to NULL, deleted_at now) and nulls the
    declared context of its attempts. The attempts, answers and results survive, still linked."""
    require_professional(user)
    session = Session()
    subject = subject_repository.get_active_owned(session, subject_id, user.id, for_update=True)
    if subject is None:
        raise SubjectNotFound()
    subject_repository.anonymize(session, subject, datetime.now(timezone.utc))
    session.commit()
