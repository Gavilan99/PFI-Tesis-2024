"""Serving by cuts, continuing, and the cut status (Feature 9, decisions of 17/10).

Against the filler bank and the stub, with the session's synthetic cut plan: what is tested here is
the serving and the rules, not the models (tests/test_trained.py).
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from app.db.models import ClassifierPrediction, Question, Response, Result, Subscription, TestAttempt
from app.db.models.enums import SubscriptionStatus
from tests.attempt_helpers import answer, answer_all, questions, start
from tests.auth_helpers import assert_error, registered
from tests.cut_helpers import answer_everything, complete, continue_, cut, give_paid_tier

CUT_STATUS_FIELDS = {
    "currentCut", "cutCount", "servedItems", "answeredItems", "nextCutItems", "canContinue",
    "currentCutAccuracy", "nextCutAccuracy", "continuedByAttemptId",
}


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


@pytest.fixture()
def plan(app):
    return app.extensions["cut_plan"]


def _rows(db_session, attempt_id) -> list[Response]:
    db_session.expire_all()
    return list(
        db_session.scalars(
            select(Response).where(Response.test_attempt_id == uuid.UUID(str(attempt_id))).order_by(Response.display_order)
        )
    )


def _bank_numbers(db_session, rows) -> list[int]:
    return [db_session.get(Question, row.question_id).display_order for row in rows]


def _attempt(db_session, attempt_id) -> TestAttempt:
    db_session.expire_all()
    return db_session.get(TestAttempt, uuid.UUID(str(attempt_id)))


def _closed_at_cut_1(api, headers) -> dict:
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    complete(api, headers, attempt["id"])
    return attempt


# --- the cut status -----------------------------------------------------------------------------


def test_the_cut_status_of_a_new_attempt(api, person, plan):
    _, headers = person
    attempt = start(api, headers)
    status = cut(api, headers, attempt["id"])
    assert set(status) == CUT_STATUS_FIELDS
    assert status == {
        "currentCut": 1,
        "cutCount": 3,
        "servedItems": 40,
        "answeredItems": 0,
        "nextCutItems": 50,
        "canContinue": False,
        "currentCutAccuracy": plan.cuts[0].estimated_accuracy,
        "nextCutAccuracy": plan.cuts[1].estimated_accuracy,
        "continuedByAttemptId": None,
    }


def test_the_cut_status_counts_answers(api, person):
    _, headers = person
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"])[:7])
    assert cut(api, headers, attempt["id"])["answeredItems"] == 7


def test_can_continue_needs_the_whole_cut_answered_and_the_paid_tier(api, person, db_session):
    user, headers = person
    attempt = start(api, headers)
    items = questions(api, headers, attempt["id"])
    answer_all(api, headers, attempt["id"], items[:-1])
    give_paid_tier(db_session, user["id"])
    assert cut(api, headers, attempt["id"])["canContinue"] is False
    answer(api, headers, attempt["id"], items[-1])
    assert cut(api, headers, attempt["id"])["canContinue"] is True


def test_without_the_paid_tier_cut_1_answered_cannot_continue(api, person):
    _, headers = person
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    status = cut(api, headers, attempt["id"])
    assert (status["answeredItems"], status["canContinue"]) == (40, False)


def test_the_last_cut_has_no_next(api, person, db_session, plan):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    attempt = start(api, headers)
    for _ in range(2):
        answer_everything(api, headers, attempt["id"])
        assert continue_(api, headers, attempt["id"]).status_code == 200
    answer_everything(api, headers, attempt["id"])
    status = cut(api, headers, attempt["id"])
    assert (status["currentCut"], status["servedItems"], status["answeredItems"]) == (3, 145, 145)
    assert status["nextCutItems"] is None and status["nextCutAccuracy"] is None
    assert status["currentCutAccuracy"] == plan.cuts[2].estimated_accuracy
    assert status["canContinue"] is False


def test_the_cut_status_of_someone_elses_attempt_is_404(api, person):
    _, headers = person
    attempt = start(api, headers)
    _, other = registered(api)
    assert_error(api.get(f"/api/attempts/{attempt['id']}/cut", headers=other), 404, "ATTEMPT_NOT_FOUND")


# --- continuing an attempt in progress ----------------------------------------------------------


def test_continuing_without_the_paid_tier_is_402_and_changes_nothing(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    assert_error(
        continue_(api, headers, attempt["id"]),
        402,
        "PAID_TIER_REQUIRED",
        "Para seguir con más preguntas necesitás una suscripción activa.",
    )
    assert len(_rows(db_session, attempt["id"])) == 40
    assert _attempt(db_session, attempt["id"]).tier.value == "free_reduced"


@pytest.mark.parametrize("kind", ["expired", "cancelled"])
def test_a_subscription_that_is_not_active_now_is_not_the_paid_tier(api, person, db_session, kind):
    user, headers = person
    if kind == "expired":
        give_paid_tier(db_session, user["id"], end=datetime.now(timezone.utc) - timedelta(minutes=1))
    else:
        give_paid_tier(db_session, user["id"])
        db_session.execute(update(Subscription).values(status=SubscriptionStatus.CANCELLED))
        db_session.commit()
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    assert_error(continue_(api, headers, attempt["id"]), 402, "PAID_TIER_REQUIRED")


def test_a_subscription_without_an_end_is_the_paid_tier(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    db_session.execute(update(Subscription).values(current_period_end=None))
    db_session.commit()
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    assert continue_(api, headers, attempt["id"]).status_code == 200


def test_a_new_attempt_is_free_reduced_even_for_someone_who_pays(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    assert start(api, headers)["tier"] == "free_reduced"


def test_continuing_with_unanswered_items_is_409(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"])[:39])
    assert_error(continue_(api, headers, attempt["id"]), 409, "CUT_INCOMPLETE")
    assert len(_rows(db_session, attempt["id"])) == 40


def test_continuing_in_progress_adds_the_next_cut_to_the_same_attempt(api, person, db_session, plan):
    user, headers = person
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    before = [(r.question_id, r.selected_option_id, r.answered_at) for r in _rows(db_session, attempt["id"])]
    give_paid_tier(db_session, user["id"])

    response = continue_(api, headers, attempt["id"])
    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == attempt["id"]
    assert body["tier"] == "paid_full" and body["status"] == "in_progress"

    rows = _rows(db_session, attempt["id"])
    assert [r.display_order for r in rows] == list(range(1, 91))
    assert [(r.question_id, r.selected_option_id, r.answered_at) for r in rows[:40]] == before
    assert _bank_numbers(db_session, rows[40:]) == list(plan.cuts[1].new_item_orders)
    assert all(r.selected_option_id is None for r in rows[40:])
    served = questions(api, headers, attempt["id"])
    assert [q["displayOrder"] for q in served] == list(range(1, 91))
    assert _attempt(db_session, attempt["id"]).tier.value == "paid_full"


def test_continuing_on_the_last_cut_is_409(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    attempt = start(api, headers)
    for _ in range(2):
        answer_everything(api, headers, attempt["id"])
        continue_(api, headers, attempt["id"])
    answer_everything(api, headers, attempt["id"])
    assert len(_rows(db_session, attempt["id"])) == 145
    assert_error(continue_(api, headers, attempt["id"]), 409, "LAST_CUT_REACHED")


def test_closing_at_cut_2_needs_cut_2_answered_and_then_classifies(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    continue_(api, headers, attempt["id"])
    assert_error(api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers), 409, "ATTEMPT_INCOMPLETE")
    answer_everything(api, headers, attempt["id"])
    assert complete(api, headers, attempt["id"])["status"] == "completed"
    predictions = db_session.scalars(
        select(ClassifierPrediction).where(ClassifierPrediction.test_attempt_id == uuid.UUID(attempt["id"]))
    ).all()
    assert len(predictions) == 4
    assert api.get(f"/api/attempts/{attempt['id']}/result", headers=headers).status_code == 200


def test_the_continue_body_carries_nothing(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    assert_error(
        api.post(f"/api/attempts/{attempt['id']}/continue", headers=headers, json={"cut": 3}), 400, "VALIDATION_ERROR"
    )
    assert api.post(f"/api/attempts/{attempt['id']}/continue", headers=headers, json={}).status_code == 200


def test_someone_elses_attempt_cannot_be_continued(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    other_user, other = registered(api)
    give_paid_tier(db_session, other_user["id"])
    assert_error(continue_(api, other, attempt["id"]), 404, "ATTEMPT_NOT_FOUND")
    assert len(_rows(db_session, attempt["id"])) == 40


def test_an_abandoned_attempt_cannot_be_continued(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    old = start(api, headers)
    answer_everything(api, headers, old["id"])
    start(api, headers)
    assert_error(continue_(api, headers, old["id"]), 409, "ATTEMPT_NOT_CONTINUABLE")
    status = cut(api, headers, old["id"])
    assert (status["answeredItems"], status["canContinue"]) == (40, False)


# --- continuing a closed attempt ----------------------------------------------------------------


def test_continuing_a_closed_attempt_without_the_paid_tier_is_402(api, person, db_session):
    _, headers = person
    attempt = _closed_at_cut_1(api, headers)
    assert_error(continue_(api, headers, attempt["id"]), 402, "PAID_TIER_REQUIRED")
    assert len(db_session.scalars(select(TestAttempt.id)).all()) == 1


def test_continuing_a_closed_attempt_starts_a_linked_one_with_its_answers(api, person, db_session, plan):
    user, headers = person
    old = _closed_at_cut_1(api, headers)
    old_rows = [(r.question_id, r.selected_option_id, r.option_order, r.display_order, r.answered_at)
                for r in _rows(db_session, old["id"])]
    old_result = db_session.scalar(select(Result).where(Result.test_attempt_id == uuid.UUID(old["id"])))
    old_result_snapshot = (old_result.id, old_result.eneatype, old_result.generated_at)
    old_closed = api.get(f"/api/attempts/{old['id']}", headers=headers).get_json()
    give_paid_tier(db_session, user["id"])

    response = continue_(api, headers, old["id"])
    assert response.status_code == 201
    new = response.get_json()
    assert new["id"] != old["id"]
    assert (new["status"], new["tier"], new["questionnaireVersion"]) == ("in_progress", "paid_full", 0)
    assert _attempt(db_session, new["id"]).continued_from_attempt_id == uuid.UUID(old["id"])

    rows = _rows(db_session, new["id"])
    assert len(rows) == 90
    copied = [(r.question_id, r.selected_option_id, r.option_order, r.display_order, r.answered_at) for r in rows[:40]]
    assert copied == old_rows
    assert [r.display_order for r in rows[40:]] == list(range(41, 91))
    assert all(r.selected_option_id is None and r.answered_at is None for r in rows[40:])
    assert _bank_numbers(db_session, rows[40:]) == list(plan.cuts[1].new_item_orders)

    # The old attempt and its result are untouched.
    assert api.get(f"/api/attempts/{old['id']}", headers=headers).get_json() == old_closed
    assert [(r.question_id, r.selected_option_id, r.option_order, r.display_order, r.answered_at)
            for r in _rows(db_session, old["id"])] == old_rows
    db_session.expire_all()
    result = db_session.scalar(select(Result).where(Result.test_attempt_id == uuid.UUID(old["id"])))
    assert (result.id, result.eneatype, result.generated_at) == old_result_snapshot

    old_status = cut(api, headers, old["id"])
    assert old_status["continuedByAttemptId"] == new["id"]
    assert old_status["canContinue"] is False
    new_status = cut(api, headers, new["id"])
    assert (new_status["currentCut"], new_status["servedItems"], new_status["answeredItems"]) == (2, 90, 40)
    assert new_status["continuedByAttemptId"] is None


def test_the_linked_attempt_closes_with_its_own_result_and_the_old_one_keeps_its_own(api, person, db_session):
    user, headers = person
    old = _closed_at_cut_1(api, headers)
    give_paid_tier(db_session, user["id"])
    new = continue_(api, headers, old["id"]).get_json()
    answer_everything(api, headers, new["id"])
    complete(api, headers, new["id"])
    results = db_session.scalars(select(Result.test_attempt_id)).all()
    assert sorted(map(str, results)) == sorted([old["id"], new["id"]])
    assert api.get(f"/api/attempts/{new['id']}/result", headers=headers).status_code == 200
    assert api.get(f"/api/attempts/{old['id']}/result", headers=headers).status_code == 200


def test_a_closed_attempt_is_continued_only_once(api, person, db_session):
    user, headers = person
    old = _closed_at_cut_1(api, headers)
    give_paid_tier(db_session, user["id"])
    assert continue_(api, headers, old["id"]).status_code == 201
    assert_error(
        continue_(api, headers, old["id"]), 409, "ATTEMPT_ALREADY_CONTINUED", "Este test ya se siguió en otro intento."
    )
    assert len(db_session.scalars(select(TestAttempt.id)).all()) == 2


def test_only_the_latest_closed_attempt_can_be_continued(api, person, db_session):
    user, headers = person
    older = _closed_at_cut_1(api, headers)
    newer = _closed_at_cut_1(api, headers)
    give_paid_tier(db_session, user["id"])
    assert cut(api, headers, older["id"])["canContinue"] is False
    assert_error(continue_(api, headers, older["id"]), 409, "ATTEMPT_NOT_CONTINUABLE")
    assert cut(api, headers, newer["id"])["canContinue"] is True


def test_continuing_a_closed_attempt_abandons_the_one_in_progress(api, person, db_session):
    user, headers = person
    old = _closed_at_cut_1(api, headers)
    in_progress = start(api, headers)
    give_paid_tier(db_session, user["id"])
    new = continue_(api, headers, old["id"]).get_json()
    assert api.get(f"/api/attempts/{in_progress['id']}", headers=headers).get_json()["status"] == "abandoned"
    assert api.get("/api/attempts/latest", headers=headers).get_json()["id"] == new["id"]


def test_a_closed_attempt_of_a_retired_version_cannot_be_continued(api, person, db_session):
    from app.services.question_bank import load_bank
    from scripts.seed_filler_bank import build_filler_bank

    user, headers = person
    old = _closed_at_cut_1(api, headers)
    load_bank(db_session, build_filler_bank(seed=7), version=1, activate=True)
    db_session.commit()
    give_paid_tier(db_session, user["id"])
    assert cut(api, headers, old["id"])["canContinue"] is False
    assert_error(continue_(api, headers, old["id"]), 409, "ATTEMPT_NOT_CONTINUABLE")


def test_the_linked_attempt_can_go_on_to_cut_3(api, person, db_session):
    user, headers = person
    old = _closed_at_cut_1(api, headers)
    give_paid_tier(db_session, user["id"])
    new = continue_(api, headers, old["id"]).get_json()
    answer_everything(api, headers, new["id"])
    complete(api, headers, new["id"])
    newest = continue_(api, headers, new["id"])
    assert newest.status_code == 201
    rows = _rows(db_session, newest.get_json()["id"])
    assert len(rows) == 145 and sum(r.selected_option_id is not None for r in rows) == 90
    assert _attempt(db_session, newest.get_json()["id"]).continued_from_attempt_id == uuid.UUID(new["id"])
