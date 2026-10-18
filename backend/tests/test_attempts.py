"""Attempts end to end (RF03, RF08, CU003): create, serve, answer, resume, complete, read.

Everything runs against the filler bank, version 0, served by the session's synthetic cut plan:
the plan's codes are resolved by `questions.display_order`, which the filler numbers 1 to 200 too.
Continuing to the next cut is in tests/test_cuts.py.
"""

import uuid

import pytest
from sqlalchemy import event, select, update

from app.db.models import Question, Response, TestAttempt
from app.services import attempts as attempts_service
from app.services.question_bank import load_bank
from scripts.seed_filler_bank import build_filler_bank
from tests.attempt_helpers import (
    ATTEMPT_FIELDS,
    RESPONSE_FIELDS,
    answer,
    answer_all,
    answer_body,
    questions,
    start,
)
from tests.auth_helpers import assert_error, registered
from tests.cut_helpers import give_paid_tier
from tests.log_helpers import captured_logs  # noqa: F401  (fixture)


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


def _served_rows(db_session, attempt_id) -> list[Response]:
    db_session.expire_all()
    return list(
        db_session.scalars(
            select(Response)
            .where(Response.test_attempt_id == uuid.UUID(attempt_id))
            .order_by(Response.display_order)
        )
    )


# --- create -------------------------------------------------------------------------------------


def test_create_returns_the_attempt_of_the_token_user(api, person):
    user, headers = person
    attempt = start(api, headers)
    assert set(attempt) == ATTEMPT_FIELDS
    assert attempt["userId"] == user["id"]
    assert attempt["subjectId"] is None
    assert attempt["tier"] == "free_reduced"
    assert attempt["questionnaireVersion"] == 0
    assert attempt["status"] == "in_progress"
    assert attempt["completedAt"] is None


def test_create_ignores_a_user_id_in_the_body(api, person):
    user, headers = person
    response = api.post("/api/attempts", headers=headers, json={"userId": str(uuid.uuid4())})
    assert response.status_code == 201
    assert response.get_json()["userId"] == user["id"]


@pytest.mark.parametrize("tier", ["paid_full", "free_reduced", None])
def test_create_rejects_a_tier_from_the_client(api, person, db_session, tier):
    _, headers = person
    response = api.post("/api/attempts", headers=headers, json={"tier": tier})
    assert_error(response, 400, "TIER_NOT_ACCEPTED")
    assert db_session.scalar(select(TestAttempt.id)) is None


def test_create_rejects_unknown_fields_and_malformed_bodies(api, person):
    _, headers = person
    assert_error(api.post("/api/attempts", headers=headers, json={"size": 60}), 400, "VALIDATION_ERROR")
    assert_error(
        api.post("/api/attempts", headers=headers, data="{nope", content_type="application/json"),
        400,
        "VALIDATION_ERROR",
    )


def test_create_requires_authentication(api, question_bank):
    assert_error(api.post("/api/attempts"), 401, "UNAUTHORIZED")


def _bank_numbers(db_session, attempt_id) -> list[int]:
    """The bank number (`questions.display_order`) of each served item, in serving order."""
    return list(
        db_session.scalars(
            select(Question.display_order)
            .join(Response, Response.question_id == Question.id)
            .where(Response.test_attempt_id == uuid.UUID(attempt_id))
            .order_by(Response.display_order)
        )
    )


def _versions(db_session, attempt_id) -> set[int]:
    return set(
        db_session.scalars(
            select(Question.version)
            .join(Response, Response.question_id == Question.id)
            .where(Response.test_attempt_id == uuid.UUID(attempt_id))
        )
    )


def test_create_serves_cut_1_the_40_items_of_the_plan_in_its_order(api, app, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    first = app.extensions["cut_plan"].cuts[0]
    assert len(questions(api, headers, attempt["id"])) == 40
    assert _bank_numbers(db_session, attempt["id"]) == list(first.new_item_orders)
    assert _versions(db_session, attempt["id"]) == {0}


def test_everyone_gets_the_same_items_in_the_same_order(api, person):
    _, headers = person
    other_headers = registered(api)[1]
    mine = questions(api, headers, start(api, headers)["id"])
    theirs = questions(api, other_headers, start(api, other_headers)["id"])
    assert [q["id"] for q in mine] == [q["id"] for q in theirs]
    assert [[o["id"] for o in q["answerOptions"]] for q in mine] == [
        [o["id"] for o in q["answerOptions"]] for q in theirs
    ]


def test_cut_1_is_stored_as_unanswered_rows_in_serving_order(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    rows = _served_rows(db_session, attempt["id"])
    assert [row.display_order for row in rows] == list(range(1, 41))
    assert all(row.selected_option_id is None and row.answered_at is None for row in rows)
    served = questions(api, headers, attempt["id"])
    assert [q["id"] for q in served] == [str(row.question_id) for row in rows]


def test_create_with_one_in_progress_abandons_it(api, person, db_session):
    _, headers = person
    first = start(api, headers)
    second = start(api, headers)
    assert api.get(f"/api/attempts/{first['id']}", headers=headers).get_json()["status"] == "abandoned"
    assert api.get(f"/api/attempts/{second['id']}", headers=headers).get_json()["status"] == "in_progress"
    statuses = db_session.scalars(select(TestAttempt.status)).all()
    assert sorted(s.value for s in statuses) == ["abandoned", "in_progress"]


def test_the_current_version_is_the_highest_active_and_versions_never_mix(api, person, db_session):
    load_bank(db_session, build_filler_bank(seed=7), version=1, activate=False)
    # Both active at once: the import script never leaves it like this, the service must not rely on it.
    db_session.execute(update(Question).values(is_active=True))
    db_session.commit()
    _, headers = person
    attempt = start(api, headers)
    assert attempt["questionnaireVersion"] == 1
    assert _versions(db_session, attempt["id"]) == {1}


def _deactivate(db_session, number: int, version: int = 0) -> None:
    db_session.execute(
        update(Question)
        .where(Question.version == version, Question.display_order == number)
        .values(is_active=False)
    )
    db_session.commit()


def test_inactive_questions_outside_the_plan_change_nothing(api, app, person, db_session):
    plan = app.extensions["cut_plan"]
    planned = set(plan.cuts[-1].model_items)
    outside = [n for n in range(1, 201) if f"Q{n:03d}" not in planned]
    db_session.execute(
        update(Question).where(Question.version == 0, Question.display_order.in_(outside)).values(is_active=False)
    )
    db_session.commit()
    _, headers = person
    attempt = start(api, headers)
    assert _bank_numbers(db_session, attempt["id"]) == list(plan.cuts[0].new_item_orders)


def test_no_active_version_is_503(api, db_session, identity):
    _, headers = registered(api)
    assert_error(api.post("/api/attempts", headers=headers), 503, "QUESTIONNAIRE_UNAVAILABLE")


def test_an_item_of_the_plan_missing_from_the_active_version_is_503_and_creates_nothing(
    api, app, person, db_session, captured_logs
):
    code = app.extensions["cut_plan"].cuts[0].serve_new_items[7]
    _deactivate(db_session, int(code[1:]))
    _, headers = person
    assert_error(api.post("/api/attempts", headers=headers), 503, "QUESTIONNAIRE_UNAVAILABLE")
    assert db_session.scalar(select(TestAttempt.id)) is None
    assert any(code in line for line in captured_logs)


def test_a_failed_create_leaves_the_attempt_in_progress_alone(api, person, app, db_session):
    _, headers = person
    attempt = start(api, headers)
    _deactivate(db_session, app.extensions["cut_plan"].cuts[0].new_item_orders[0])
    assert_error(api.post("/api/attempts", headers=headers), 503, "QUESTIONNAIRE_UNAVAILABLE")
    assert api.get(f"/api/attempts/{attempt['id']}", headers=headers).get_json()["status"] == "in_progress"


# --- serve and resume ---------------------------------------------------------------------------


def test_reloading_serves_the_same_items_in_the_same_order(api, person):
    _, headers = person
    attempt = start(api, headers)
    assert questions(api, headers, attempt["id"]) == questions(api, headers, attempt["id"])


def test_display_orders_are_the_served_positions(api, person):
    _, headers = person
    served = questions(api, headers, start(api, headers)["id"])
    assert [q["displayOrder"] for q in served] == list(range(1, len(served) + 1))
    for question in served:
        options = question["answerOptions"]
        assert [o["displayOrder"] for o in options] == list(range(1, len(options) + 1))
        assert {o["questionId"] for o in options} == {question["id"]}


def test_resume_after_answering_half(api, person):
    """Create, answer half, ask again: same subset, same order, same answers."""
    _, headers = person
    attempt = start(api, headers)
    before = questions(api, headers, attempt["id"])
    half = before[: len(before) // 2]
    chosen = {}
    for k, question in enumerate(half):
        position = k % len(question["answerOptions"])
        assert answer(api, headers, attempt["id"], question, position).status_code == 200
        chosen[question["id"]] = question["answerOptions"][position]["id"]

    after = questions(api, headers, attempt["id"])
    assert after == before
    responses = api.get(f"/api/attempts/{attempt['id']}/responses", headers=headers).get_json()
    assert {r["questionId"]: r["selectedOptionId"] for r in responses} == chosen
    # In serving order, which is what the screen walks.
    assert [r["questionId"] for r in responses] == [q["id"] for q in half]

    latest = api.get("/api/attempts/latest", headers=headers).get_json()
    assert latest["id"] == attempt["id"] and latest["status"] == "in_progress"


# --- answer -------------------------------------------------------------------------------------


def test_answer_returns_the_test_response(api, person):
    _, headers = person
    attempt = start(api, headers)
    question = questions(api, headers, attempt["id"])[0]
    response = answer(api, headers, attempt["id"], question, 1)
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == RESPONSE_FIELDS
    assert body["testAttemptId"] == attempt["id"]
    assert body["questionId"] == question["id"]
    assert body["selectedOptionId"] == question["answerOptions"][1]["id"]
    assert body["freeTextResponse"] is None and body["orderingResponse"] is None
    assert body["answeredAt"]


def test_answering_again_replaces_the_previous_answer(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    question = questions(api, headers, attempt["id"])[0]
    first = answer(api, headers, attempt["id"], question, 0).get_json()
    second = answer(api, headers, attempt["id"], question, 2).get_json()
    assert second["id"] == first["id"]
    responses = api.get(f"/api/attempts/{attempt['id']}/responses", headers=headers).get_json()
    assert len(responses) == 1
    assert responses[0]["selectedOptionId"] == question["answerOptions"][2]["id"]
    assert len(_served_rows(db_session, attempt["id"])) == 40


def test_only_answered_items_are_listed(api, person):
    _, headers = person
    attempt = start(api, headers)
    assert api.get(f"/api/attempts/{attempt['id']}/responses", headers=headers).get_json() == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"freeTextResponse": "texto"},
        {"orderingResponse": ["a", "b"]},
        {"orderingResponse": []},
        {"selectedOptionId": None},
        {"selectedOptionId": "no-es-un-uuid"},
        {"questionId": None},
        {"groupLabel": "gut"},
        {"userId": "cualquiera"},
        {"testAttemptId": "cualquiera"},
    ],
)
def test_answer_body_is_new_response_input_and_nothing_else(api, person, overrides):
    _, headers = person
    attempt = start(api, headers)
    question = questions(api, headers, attempt["id"])[0]
    body = answer_body(question["id"], question["answerOptions"][0]["id"], **overrides)
    response = api.post(f"/api/attempts/{attempt['id']}/responses", headers=headers, json=body)
    assert_error(response, 400, "VALIDATION_ERROR")


@pytest.mark.parametrize(
    "missing", ["questionId", "selectedOptionId", "freeTextResponse", "orderingResponse"]
)
def test_answer_body_needs_every_field(api, person, missing):
    _, headers = person
    attempt = start(api, headers)
    question = questions(api, headers, attempt["id"])[0]
    body = answer_body(question["id"], question["answerOptions"][0]["id"])
    del body[missing]
    response = api.post(f"/api/attempts/{attempt['id']}/responses", headers=headers, json=body)
    assert_error(response, 400, "VALIDATION_ERROR")


def test_a_question_outside_the_subset_is_rejected(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    served = {q["id"] for q in questions(api, headers, attempt["id"])}
    outside = db_session.scalars(select(Question).where(Question.version == 0)).all()
    question = next(q for q in outside if str(q.id) not in served)
    body = answer_body(str(question.id), str(question.answer_options[0].id))
    response = api.post(f"/api/attempts/{attempt['id']}/responses", headers=headers, json=body)
    assert_error(response, 400, "QUESTION_NOT_IN_ATTEMPT")


def test_an_option_of_another_question_is_rejected(api, person):
    _, headers = person
    attempt = start(api, headers)
    first, second = questions(api, headers, attempt["id"])[:2]
    body = answer_body(first["id"], second["answerOptions"][0]["id"])
    response = api.post(f"/api/attempts/{attempt['id']}/responses", headers=headers, json=body)
    assert_error(response, 400, "OPTION_NOT_IN_QUESTION")


def test_an_abandoned_attempt_takes_no_answers(api, person):
    _, headers = person
    old = start(api, headers)
    question = questions(api, headers, old["id"])[0]
    start(api, headers)
    assert_error(answer(api, headers, old["id"], question), 409, "ATTEMPT_NOT_IN_PROGRESS")


def test_a_completed_attempt_takes_no_answers(api, person):
    _, headers = person
    attempt = start(api, headers)
    items = questions(api, headers, attempt["id"])
    answer_all(api, headers, attempt["id"], items)
    assert api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers).status_code == 200
    assert_error(answer(api, headers, attempt["id"], items[0], 1), 409, "ATTEMPT_NOT_IN_PROGRESS")


# --- complete -----------------------------------------------------------------------------------


def test_completing_an_incomplete_attempt_is_409_and_changes_nothing(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    items = questions(api, headers, attempt["id"])
    answer_all(api, headers, attempt["id"], items[:-1])
    before = api.get(f"/api/attempts/{attempt['id']}", headers=headers).get_json()

    response = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert_error(
        response,
        409,
        "ATTEMPT_INCOMPLETE",
        "Quedan preguntas sin responder: el test no se puede cerrar todavía.",
    )
    assert api.get(f"/api/attempts/{attempt['id']}", headers=headers).get_json() == before
    assert len(api.get(f"/api/attempts/{attempt['id']}/responses", headers=headers).get_json()) == 39


def test_completing_twice_returns_the_same_and_duplicates_nothing(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))

    first = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    second = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.get_json() == second.get_json()
    assert first.get_json()["status"] == "completed"
    assert first.get_json()["completedAt"]
    assert len(db_session.scalars(select(TestAttempt.id)).all()) == 1
    assert len(_served_rows(db_session, attempt["id"])) == 40


def test_the_completion_hook_runs_once(api, person, monkeypatch):
    calls = []
    monkeypatch.setattr(
        attempts_service, "_after_completion", lambda session, attempt, classifier: calls.append(attempt.id)
    )
    _, headers = person
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))
    api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert [str(c) for c in calls] == [attempt["id"]]


def test_an_abandoned_attempt_cannot_be_completed(api, person):
    _, headers = person
    old = start(api, headers)
    start(api, headers)
    response = api.post(f"/api/attempts/{old['id']}/complete", headers=headers)
    assert_error(response, 409, "ATTEMPT_NOT_IN_PROGRESS")


# --- reads --------------------------------------------------------------------------------------


def test_latest_is_null_without_attempts(api, person):
    _, headers = person
    response = api.get("/api/attempts/latest", headers=headers)
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() is None


def test_latest_is_the_newest_whatever_its_status(api, person):
    _, headers = person
    start(api, headers)
    newest = start(api, headers)
    assert api.get("/api/attempts/latest", headers=headers).get_json() == newest


def test_history_is_newest_first(api, person):
    _, headers = person
    created = [start(api, headers)["id"] for _ in range(3)]
    history = api.get("/api/attempts", headers=headers).get_json()
    assert [a["id"] for a in history] == created[::-1]
    assert [a["status"] for a in history] == ["in_progress", "abandoned", "abandoned"]


def test_history_is_empty_without_attempts(api, person):
    _, headers = person
    assert api.get("/api/attempts", headers=headers).get_json() == []


def test_get_attempt_that_does_not_exist_is_404(api, person):
    _, headers = person
    assert_error(api.get(f"/api/attempts/{uuid.uuid4()}", headers=headers), 404, "ATTEMPT_NOT_FOUND")
    assert_error(api.get("/api/attempts/no-es-un-uuid", headers=headers), 404, "NOT_FOUND")


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/attempts"),
        ("get", "/api/attempts/latest"),
        ("get", "/api/attempts/{id}"),
        ("get", "/api/attempts/{id}/questions"),
        ("get", "/api/attempts/{id}/responses"),
        ("post", "/api/attempts/{id}/responses"),
        ("post", "/api/attempts/{id}/complete"),
        ("post", "/api/attempts/{id}/continue"),
        ("get", "/api/attempts/{id}/cut"),
    ],
)
def test_every_endpoint_requires_authentication(api, question_bank, method, path):
    response = getattr(api, method)(path.format(id=uuid.uuid4()))
    assert_error(response, 401, "UNAUTHORIZED")


def _count_queries(app, call) -> list[str]:
    statements = []
    engine = app.extensions["sqlalchemy_engine"]

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        call()
    finally:
        event.remove(engine, "before_cursor_execute", record)
    return statements


def test_serving_takes_the_same_few_queries_whatever_the_cut(api, app, person, db_session):
    """Authentication, ownership, the items, their options: four queries for 40 items or for 90."""
    user, headers = person
    small = start(api, headers)  # abandoned by the next start, and still readable
    large = start(api, headers)
    answer_all(api, headers, large["id"], questions(api, headers, large["id"]))
    give_paid_tier(db_session, user["id"])
    assert api.post(f"/api/attempts/{large['id']}/continue", headers=headers).status_code == 200

    counts = []
    for attempt, size in ((small, 40), (large, 90)):
        served = []
        statements = _count_queries(app, lambda: served.extend(questions(api, headers, attempt["id"])))
        assert len(served) == size
        counts.append(len([s for s in statements if s.lstrip().upper().startswith("SELECT")]))
    assert counts == [4, 4]
