"""Test attempts: create, serve by cuts, answer, continue, resume, complete and read them
(RF03, RF08, RNF10, CU003).

Since Feature 9 (decision of 17/10) the test is served in three fixed, nested cuts of 40, 90 and 145
items (`app.ml.cut_plan`). Everyone gets the same items in the same order, with the options in the
bank's order, which is what the pilot the models were trained on saw. Creating an attempt serves cut 1;
continuing adds the next cut's rows, numbered after the ones already served.

Continuing:
- an attempt in progress, with its cut fully answered, gets the next cut's rows in place;
- a closed attempt is never reopened and its result never overwritten: the test goes on in a new
  attempt linked to it (`continued_from_attempt_id`), which starts with its answers copied. Only from
  the person's latest closed attempt, once, and while its questionnaire version is still active;
- the second and third cuts require the paid tier (`app.services.tiers`). An attempt that continues to
  a paid cut becomes `paid_full`.

The instrument's answer key never leaves this module towards the client: nothing here returns
`group_label` or `grouping_system`, and the read paths do not even load them.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import Response, TestAttempt, User
from app.db.models.enums import AttemptStatus, AttemptTier, QuestionType
from app.db.session import Session
from app.exceptions import (
    AppError,
    AttemptAlreadyContinued,
    AttemptIncomplete,
    AttemptNotContinuable,
    AttemptNotFound,
    AttemptNotInProgress,
    CutIncomplete,
    LastCutReached,
    OptionNotInQuestion,
    PaidTierRequired,
    QuestionNotInAttempt,
    QuestionnaireUnavailable,
)
from app.ml.classification import Classifier
from app.ml.cut_plan import Cut, CutPlan, question_code
from app.repositories import attempt_repository
from app.services import results, tiers

logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class CutState:
    """Where an attempt stands in the cuts. The accuracy is the estimated eneatype accuracy of a cut:
    public on purpose, it is the number the product shows. Nothing else of the models is."""

    current_cut: int
    cut_count: int
    served_items: int
    answered_items: int
    next_cut_items: int | None
    can_continue: bool
    current_cut_accuracy: float
    next_cut_accuracy: float | None
    continued_by_attempt_id: uuid.UUID | None


def create_attempt(user: User, plan: CutPlan) -> TestAttempt:
    """Start an attempt for `user` with cut 1, abandoning the one in progress, in one transaction."""
    session = Session()
    try:
        attempt_repository.lock_user(session, user.id)
        attempt_repository.abandon_in_progress(session, user.id)

        version = attempt_repository.current_version(session)
        if version is None:
            logger.error("No active questionnaire version: attempts cannot be created")
            raise QuestionnaireUnavailable()
        items = _resolve_cut(session, version, plan.cuts[0])

        attempt = attempt_repository.insert_attempt(
            session, user_id=user.id, tier=tiers.new_attempt_tier(), version=version
        )
        attempt_repository.insert_served_items(session, attempt.id, items)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return attempt


def continue_attempt(user: User, attempt_id: uuid.UUID, plan: CutPlan) -> tuple[TestAttempt, bool]:
    """Serve the next cut. Returns the attempt the test goes on in, and whether it is a new one."""
    session = Session()
    try:
        # Serializes with creating an attempt: both may abandon the one in progress.
        attempt_repository.lock_user(session, user.id)
        attempt = _owned(session, user, attempt_id, for_update=True)
        cut, served, answered = _cut_of(session, plan, attempt)
        following = plan.next_cut(cut)
        blocked = _continuation_block(session, user, attempt, following, served, answered)
        if blocked is not None:
            raise blocked

        items = _resolve_cut(session, attempt.questionnaire_version, following)
        tier = attempt.tier
        if tiers.required_tier(following.number) is AttemptTier.PAID_FULL:
            tier = AttemptTier.PAID_FULL
        if attempt.status is AttemptStatus.IN_PROGRESS:
            if tier is not attempt.tier:
                attempt_repository.set_tier(session, attempt, tier)
            attempt_repository.insert_served_items(session, attempt.id, items, first=served + 1)
            target, created = attempt, False
        else:
            attempt_repository.abandon_in_progress(session, user.id)
            target = attempt_repository.insert_attempt(
                session,
                user_id=user.id,
                tier=tier,
                version=attempt.questionnaire_version,
                continued_from=attempt.id,
            )
            attempt_repository.copy_responses(session, attempt.id, target.id)
            attempt_repository.insert_served_items(session, target.id, items, first=served + 1)
            created = True
        session.commit()
    except Exception:
        session.rollback()
        raise
    return target, created


def cut_state(user: User, attempt_id: uuid.UUID, plan: CutPlan) -> CutState:
    """For the screen between cuts and the result screen: in progress, closed or abandoned alike."""
    session = Session()
    attempt = _owned(session, user, attempt_id)
    cut, served, answered = _cut_of(session, plan, attempt)
    following = plan.next_cut(cut)
    return CutState(
        current_cut=cut.number,
        cut_count=len(plan.cuts),
        served_items=served,
        answered_items=answered,
        next_cut_items=len(following.serve_new_items) if following else None,
        can_continue=_continuation_block(session, user, attempt, following, served, answered) is None,
        current_cut_accuracy=cut.estimated_accuracy,
        next_cut_accuracy=following.estimated_accuracy if following else None,
        continued_by_attempt_id=attempt_repository.continuation_of(session, attempt.id),
    )


def _continuation_block(
    session, user: User, attempt: TestAttempt, following: Cut | None, served: int, answered: int
) -> AppError | None:
    """Why the attempt cannot go on to the next cut, or None if it can. The one rule behind both the
    continue route and `canContinue`. State first; the tier only matters when the rest allows it."""
    if attempt.status is AttemptStatus.ABANDONED:
        return AttemptNotContinuable()
    if following is None:
        return LastCutReached()
    if answered < served:
        return CutIncomplete()
    if attempt.status is AttemptStatus.COMPLETED:
        if attempt_repository.continuation_of(session, attempt.id) is not None:
            return AttemptAlreadyContinued()
        if attempt_repository.latest_completed_for_user(session, user.id) != attempt.id:
            return AttemptNotContinuable()
        if attempt_repository.current_version(session) != attempt.questionnaire_version:
            return AttemptNotContinuable()
    if not tiers.may_take_cut(session, user.id, following.number):
        return PaidTierRequired()
    return None


def _cut_of(session, plan: CutPlan, attempt: TestAttempt) -> tuple[Cut, int, int]:
    served, answered = attempt_repository.served_and_answered(session, attempt.id)
    cut = plan.cut_by_size(served)
    if cut is None:
        # An attempt served before the cuts existed (the Feature 3 subsets of 20 or 60).
        logger.error("Attempt %s has %s served items: no cut of the plan has that size", attempt.id, served)
        raise AttemptNotContinuable()
    return cut, served, answered


def _resolve_cut(session, version: int, cut: Cut) -> list[tuple[uuid.UUID, list[uuid.UUID]]]:
    """The cut's new items as (question id, option ids in bank order), in serving order. A code that is
    not an active question of `version` stops it: nothing is created."""
    orders = list(cut.new_item_orders)
    ids = attempt_repository.active_question_ids_by_order(session, version, orders)
    missing = [question_code(order) for order in orders if order not in ids]
    if missing:
        logger.error(
            "Questionnaire version %s lacks %s active items of cut %s (%s items): %s",
            version, len(missing), cut.number, cut.size, ", ".join(missing),
        )
        raise QuestionnaireUnavailable()
    bank_order = attempt_repository.option_ids_in_bank_order(session, list(ids.values()))
    return [(ids[order], bank_order[ids[order]]) for order in orders]


def served_questions(user: User, attempt_id: uuid.UUID) -> list[ServedQuestion]:
    """Everything served so far in one go, in the attempt's order. `display_order` is the position
    served, for questions and for options alike; options are served in the bank's order."""
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
    """Record (or replace) the answer to one served question. Only the option id is stored;
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

    Rejected while any served item is unanswered: an incomplete attempt marked completed would
    contaminate the dataset. It closes in whatever cut it is in.
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
