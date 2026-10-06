"""Every ORM model, imported here so they register on Base.metadata (Alembic depends on it)."""

from app.db.models.billing import Payment, Subscription
from app.db.models.questionnaire import AnswerOption, Question, Response, TestAttempt
from app.db.models.results import ClassifierPrediction, Feedback, Result
from app.db.models.users import Subject, User

__all__ = [
    "AnswerOption",
    "ClassifierPrediction",
    "Feedback",
    "Payment",
    "Question",
    "Response",
    "Result",
    "Subject",
    "Subscription",
    "TestAttempt",
    "User",
]
