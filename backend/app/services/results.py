"""Results (RF04, RF05, RF08, CU004): computed once when an attempt closes, read afterwards.

Closing an attempt classifies its answers through the seam in `app.ml` and stores, in the same
transaction that marks it completed, the four `classifier_predictions` rows and the `results` row.
If the classification fails, nothing is stored and the attempt stays in progress.

What is stored and never leaves: the four predicted groups, their probabilities, the model version
and the confidence margin. The client gets the eneatype and the description, and nothing derived from
the rest.
"""

import logging
import uuid

from app.db.models import Result, TestAttempt, User
from app.db.session import Session
from app.exceptions import ResultNotFound, ResultNotGenerated
from app.ml.classification import Classifier, validate
from app.repositories import result_repository
from app.services.result_descriptions import description_for

logger = logging.getLogger(__name__)


def record_result(session, attempt: TestAttempt, classifier: Classifier) -> Result:
    """Classify a closing attempt and store what came out. Runs inside the caller's transaction."""
    answers = result_repository.classification_inputs(session, attempt.id)
    try:
        classification = validate(classifier.classify(answers))
    except Exception:
        logger.exception(
            "Classification failed for attempt %s (model %s): the attempt stays in progress",
            attempt.id, getattr(classifier, "model_version", "?"),
        )
        raise ResultNotGenerated() from None
    return result_repository.insert_classification(
        session, attempt.id, classification, description_for(classification.eneatype)
    )


def get_result(user: User, attempt_id: uuid.UUID) -> Result:
    """The result of the user's own closed attempt. Anything else is the same 404."""
    result = result_repository.result_of_owned_completed(Session(), attempt_id, user.id)
    if result is None:
        raise ResultNotFound()
    return result
