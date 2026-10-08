"""Test attempts: create, serve, answer, resume, complete and read them (RF03, RF08, RNF10, CU003).

The instrument's answer key never leaves this module towards the client: nothing here returns
`group_label` or `grouping_system`, and the read paths do not even load them. It hides in two more
places, and both are closed when the attempt is created:

- Option order. Each scenario item covers its system's three groups once, so a fixed order would
  make the position the group. Scenario options are shuffled per attempt; Likert options never are,
  because their order is the signal. The order served is stored in `responses.option_order`.
- Question order. The subset is shuffled as a whole, so an item's position says nothing about its
  system.

All of it is decided once, at creation, and stored: reloading serves the same items in the same order.
"""

import logging
import random
import uuid
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import Response, TestAttempt, User
from app.db.models.enums import AttemptStatus, AttemptTier, GroupingSystem, QuestionType
from app.db.session import Session
from app.exceptions import (
    AttemptIncomplete,
    AttemptNotFound,
    AttemptNotInProgress,
    OptionNotInQuestion,
    QuestionNotInAttempt,
    QuestionnaireUnavailable,
)
from app.ml.classification import Classifier
from app.repositories import attempt_repository
from app.services import results
from app.services.tiers import resolve_attempt_tier

logger = logging.getLogger(__name__)

# Unpredictable on purpose: a seeded generator would make the subset and the option order guessable.
_rng = random.SystemRandom()


@dataclass(frozen=True)
class ServedOption:
    id: uuid.UUID
    question_id: uuid.UUID
    option_text: str
    display_order: int


@dataclass(frozen=True)
class ServedQuestion:
    id: uuid.UUID
    question_type: QuestionType
    prompt_text: str
    display_order: int
    answer_options: list[ServedOption]


def create_attempt(user: User, subset_sizes: Mapping[AttemptTier, int]) -> TestAttempt:
    """Start an attempt for `user`, abandoning the one in progress if there is one, in one transaction."""
    session = Session()
    try:
        attempt_repository.lock_user(session, user.id)
        attempt_repository.abandon_in_progress(session, user.id)

        tier = resolve_attempt_tier(user)
        version = attempt_repository.current_version(session)
        if version is None:
            logger.error("No active questionnaire version: attempts cannot be created")
            raise QuestionnaireUnavailable()
        items = _pick_subset(session, version, subset_sizes[tier])

        attempt = attempt_repository.insert_attempt(session, user_id=user.id, tier=tier, version=version)
        attempt_repository.insert_served_items(session, attempt.id, items)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return attempt


def _pick_subset(session, version: int, size: int) -> list[tuple[uuid.UUID, list[uuid.UUID]]]:
    """`size` active questions of `version`, the same number from each grouping system, shuffled,
    each with the order its options will be served in."""
    per_system = size // len(GroupingSystem)
    pool: dict[GroupingSystem, list] = defaultdict(list)
    for question in attempt_repository.active_questions(session, version):
        pool[question.grouping_system].append(question)

    short = {system.value: len(pool[system]) for system in GroupingSystem if len(pool[system]) < per_system}
    if short:
        logger.error(
            "Questionnaire version %s cannot fill a subset of %s (%s per system); active questions: %s",
            version, size, per_system, short,
        )
        raise QuestionnaireUnavailable()

    chosen = [question for system in GroupingSystem for question in _rng.sample(pool[system], per_system)]
    _rng.shuffle(chosen)

    bank_order = attempt_repository.option_ids_in_bank_order(session, [q.id for q in chosen])
    items = []
    for question in chosen:
        order = bank_order[question.id]
        if question.question_type is QuestionType.SCENARIO:
            order = _rng.sample(order, len(order))
        items.append((question.id, order))
    return items


def served_questions(user: User, attempt_id: uuid.UUID) -> list[ServedQuestion]:
    """The whole subset in one go, in the attempt's order. `display_order` is the position served,
    for questions and for options alike, never the bank's."""
    session = Session()
    attempt = _owned(session, user, attempt_id)
    rows = attempt_repository.served_questions(session, attempt.id)
    texts = attempt_repository.option_texts(session, [row.id for row in rows])
    return [
        ServedQuestion(
            id=row.id,
            question_type=row.question_type,
            prompt_text=row.prompt_text,
            display_order=row.display_order,
            answer_options=[
                ServedOption(
                    id=option_id, question_id=row.id, option_text=texts[option_id], display_order=position
                )
                for position, option_id in enumerate(row.option_order, start=1)
            ],
        )
        for row in rows
    ]


def submit_response(
    user: User, attempt_id: uuid.UUID, *, question_id: uuid.UUID, selected_option_id: uuid.UUID
) -> Response:
    """Record (or replace) the answer to one question of the subset. Only the option id is stored;
    the group it maps to is resolved by the server when it is needed, never here."""
    session = Session()
    try:
        attempt = _owned(session, user, attempt_id, for_update=True)
        if attempt.status is not AttemptStatus.IN_PROGRESS:
            raise AttemptNotInProgress()
        response = attempt_repository.get_response(session, attempt.id, question_id, for_update=True)
        if response is None:
            raise QuestionNotInAttempt()
        if selected_option_id not in response.option_order:
            raise OptionNotInQuestion()
        attempt_repository.record_answer(session, response, selected_option_id, datetime.now(timezone.utc))
        session.commit()
    except Exception:
        session.rollback()
        raise
    return response


def answered_responses(user: User, attempt_id: uuid.UUID) -> list[Response]:
    """What resuming needs: only the items already answered. Pre-created empty rows stay out."""
    session = Session()
    attempt = _owned(session, user, attempt_id)
    return attempt_repository.answered_responses(session, attempt.id)


def complete_attempt(user: User, attempt_id: uuid.UUID, classifier: Classifier) -> TestAttempt:
    """Close the attempt and compute its result. Idempotent: closing a completed attempt returns it
    unchanged, and neither classifies again nor touches the result it already has.

    Rejected while any item of the subset is unanswered: an incomplete attempt marked completed would
    contaminate the dataset. The interface never tries it.
    """
    session = Session()
    try:
        attempt = _owned(session, user, attempt_id, for_update=True)
        if attempt.status is AttemptStatus.COMPLETED:
            session.rollback()
            return attempt
        if attempt.status is not AttemptStatus.IN_PROGRESS:
            raise AttemptNotInProgress()
        if attempt_repository.unanswered_count(session, attempt.id):
            raise AttemptIncomplete()
        attempt_repository.mark_completed(session, attempt)
        _after_completion(session, attempt, classifier)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return attempt


def _after_completion(session, attempt: TestAttempt, classifier: Classifier) -> None:
    """Classify the attempt's answers and persist `classifier_predictions` and `results`.

    Runs exactly once per attempt, inside the transaction that marks it completed, so an attempt is
    never left completed without its result: if the classification fails, the whole close is rolled
    back. The repeated call of an idempotent complete returns before reaching it.
    """
    results.record_result(session, attempt, classifier)


def latest_attempt(user: User) -> TestAttempt | None:
    return attempt_repository.latest_for_user(Session(), user.id)


def get_attempt(user: User, attempt_id: uuid.UUID) -> TestAttempt:
    return _owned(Session(), user, attempt_id)


def attempt_history(user: User) -> list[TestAttempt]:
    """Every attempt of the user, newest first."""
    return attempt_repository.history_for_user(Session(), user.id)


def _owned(session, user: User, attempt_id: uuid.UUID, *, for_update: bool = False) -> TestAttempt:
    """The user's own attempt. Someone else's, or one that does not exist, is the same 404."""
    attempt = attempt_repository.get_owned(session, attempt_id, user.id, for_update=for_update)
    if attempt is None:
        raise AttemptNotFound()
    return attempt
