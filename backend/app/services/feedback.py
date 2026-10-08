"""Feedback (RF06): a rating and an optional comment, general or tied to one of the user's attempts.

Never shown back to the user; it feeds the pilot. The user comes from the token. Deleting the account
nulls the comment and keeps the rating (app.repositories.user_repository.anonymize).
"""

import uuid

from app.db.models import User
from app.db.session import Session
from app.exceptions import AttemptNotFound
from app.repositories import attempt_repository, feedback_repository


def submit_feedback(user: User, *, test_attempt_id: uuid.UUID | None, rating: int, comment: str | None) -> None:
    session = Session()
    # Someone else's attempt answers like one that does not exist.
    if test_attempt_id is not None and attempt_repository.get_owned(session, test_attempt_id, user.id) is None:
        raise AttemptNotFound()
    feedback_repository.insert(
        session, user_id=user.id, test_attempt_id=test_attempt_id, rating=rating, comment=comment
    )
    session.commit()
