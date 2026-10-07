from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Feedback, Subject, TestAttempt, User


def get_live_by_sub(session: Session, sub: str, *, for_update: bool = False) -> User | None:
    query = select(User).where(User.cognito_sub == sub, User.is_deleted.is_(False))
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


def live_email_exists(session: Session, email: str) -> bool:
    """`email` must already be normalized: the unique index compares `lower(email)`."""
    return session.scalar(
        select(select(User.id).where(User.email == email, User.is_deleted.is_(False)).exists())
    )


def insert_if_absent(session: Session, *, sub: str, email: str, display_name: str | None) -> User | None:
    """Insert the row for `sub` unless one already exists, and return the live row for `sub`.

    ON CONFLICT DO NOTHING makes two concurrent first requests of the same new user safe: the second
    insert waits for the first, then does nothing, and both read the same row. Returns None when the
    conflict was on the email instead (a different live account already holds it).
    """
    session.execute(
        insert(User)
        .values(cognito_sub=sub, email=email, display_name=display_name)
        .on_conflict_do_nothing()
    )
    return get_live_by_sub(session, sub)


def update_profile(session: Session, user: User, changes: dict) -> User:
    for field, value in changes.items():
        setattr(user, field, value)
    session.flush()
    return user


def anonymize(session: Session, user: User, now: datetime) -> None:
    """Apply the "Borrado de cuenta" table of CLAUDE.md. Nothing is deleted physically.

    Kept: demographics, attempts, responses, predictions, results, feedback ratings, subscriptions,
    payments. Nulled: what identifies the person.
    """
    user.email = None
    user.display_name = None
    user.cognito_sub = None
    user.profession_context = None
    user.is_deleted = True
    user.deleted_at = now

    own_attempts = select(TestAttempt.id).where(TestAttempt.user_id == user.id)
    session.execute(
        update(Feedback)
        .where(or_(Feedback.user_id == user.id, Feedback.test_attempt_id.in_(own_attempts)))
        .values(comment=None)
    )
    session.execute(
        update(Subject)
        .where(Subject.professional_user_id == user.id)
        .values(label=None, context_data=None)
    )
    session.flush()
