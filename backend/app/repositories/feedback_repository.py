import uuid

from sqlalchemy.orm import Session

from app.db.models import Feedback


def insert(
    session: Session, *, user_id: uuid.UUID, test_attempt_id: uuid.UUID | None, rating: int, comment: str | None
) -> Feedback:
    feedback = Feedback(user_id=user_id, test_attempt_id=test_attempt_id, rating=rating, comment=comment)
    session.add(feedback)
    session.flush()
    return feedback
