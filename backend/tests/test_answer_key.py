"""The instrument's answer key never leaves the server. Two layers, each with its own tests, plus the
tests that prove the suite-wide guard (tests/leak_guard.py) fails when something leaks.

(a) Keys: `group_label` and `grouping_system` are in no response, in any casing.
(b) Values: no group label or system name of the canonical vocabulary is in any response.

(c) Order, since Feature 9, is fixed and not a secret: the bank with its groups is public in the
repository (`research/bank/`), every option is served in the bank's order (the order the pilot saw,
which the models were trained on), and the items in the order of the cut plan, which alternates the
four systems (`serve_order`). Its tests check exactly that.
"""

import uuid

import pytest
from flask import Flask, jsonify
from sqlalchemy import select

from app.blueprints.attempts.schemas import AnswerOptionOut, QuestionOut
from app.blueprints.results.schemas import ResultOut
from app.db.models import AnswerOption, Question, Response
from app.db.models.enums import GROUP_LABELS, GroupingSystem
from tests import leak_guard
from tests.attempt_helpers import OPTION_FIELDS, QUESTION_FIELDS, answer, answer_all, questions, start
from tests.auth_helpers import registered
from tests.cut_helpers import load_real_bank

SYSTEM_NAMES = {system.value for system in GroupingSystem}
FORBIDDEN_KEY_SPELLINGS = ("group_label", "groupLabel", "grouping_system", "groupingSystem")
# Stored with every result and never exposed (PDR). Both forms, as the guard sees them.
CLASSIFIER_OUTPUT_SPELLINGS = (
    "probabilities", "predicted_group", "predictedGroup", "confidence_margin", "confidenceMargin",
    "model_version", "modelVersion",
)


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


def _every_attempt_response(api, headers) -> list:
    """One response of every attempt endpoint, along a full attempt."""
    created = api.post("/api/attempts", headers=headers)
    attempt_id = created.get_json()["id"]
    served = api.get(f"/api/attempts/{attempt_id}/questions", headers=headers)
    items = served.get_json()
    collected = [created, served]
    for item in items:
        collected.append(answer(api, headers, attempt_id, item))
    collected += [
        api.get(f"/api/attempts/{attempt_id}/responses", headers=headers),
        api.get(f"/api/attempts/{attempt_id}/cut", headers=headers),
        api.post(f"/api/attempts/{attempt_id}/complete", headers=headers),
        api.get(f"/api/attempts/{attempt_id}/cut", headers=headers),
        api.get(f"/api/attempts/{attempt_id}/result", headers=headers),
        api.get(f"/api/attempts/{attempt_id}", headers=headers),
        api.get("/api/attempts/latest", headers=headers),
        api.get("/api/attempts", headers=headers),
    ]
    assert all(r.status_code in (200, 201) for r in collected)
    return collected


def _strings(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield key
            yield from _strings(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _strings(item)
    elif isinstance(payload, str):
        yield payload


def _bank_rows(db_session) -> dict[uuid.UUID, tuple]:
    """Question id -> (system, type, bank display order, [(option id, group)] in bank order)."""
    db_session.expire_all()
    rows = {}
    for question in db_session.scalars(select(Question)):
        in_bank_order = sorted(question.answer_options, key=lambda o: o.display_order)
        options = [(o.id, o.group_label) for o in in_bank_order]
        rows[question.id] = (
            question.grouping_system, question.question_type, question.display_order, options
        )
    return rows


# --- (a) keys -----------------------------------------------------------------------------------


def test_a_the_output_schemas_have_exactly_the_contract_fields():
    assert {f.alias for f in QuestionOut.model_fields.values()} == QUESTION_FIELDS
    assert {f.alias for f in AnswerOptionOut.model_fields.values()} == OPTION_FIELDS


def test_a_no_response_carries_the_answer_key_fields(api, person):
    _, headers = person
    for response in _every_attempt_response(api, headers):
        body = response.get_data(as_text=True)
        for spelling in FORBIDDEN_KEY_SPELLINGS + CLASSIFIER_OUTPUT_SPELLINGS:
            assert spelling not in body
        assert leak_guard.find_leaks(response.get_json()) == []


def test_a_questions_and_options_have_exactly_the_contract_fields(api, person):
    _, headers = person
    for question in questions(api, headers, start(api, headers)["id"]):
        assert set(question) == QUESTION_FIELDS
        for option in question["answerOptions"]:
            assert set(option) == OPTION_FIELDS


# --- (b) values ---------------------------------------------------------------------------------


def test_b_no_response_carries_a_canonical_label_or_system_as_a_value(api, person):
    _, headers = person
    for response in _every_attempt_response(api, headers):
        strings = {s.strip().lower() for s in _strings(response.get_json())}
        assert not strings & set(GROUP_LABELS)
        assert not strings & SYSTEM_NAMES


# --- (c) order ----------------------------------------------------------------------------------


def test_c_every_option_is_served_in_the_banks_order_scenario_and_likert(api, person, db_session):
    _, headers = person
    bank = _bank_rows(db_session)
    served = questions(api, headers, start(api, headers)["id"])
    types = set()
    for item in served:
        _, question_type, _, options = bank[uuid.UUID(item["id"])]
        types.add(question_type)
        assert [uuid.UUID(o["id"]) for o in item["answerOptions"]] == [option_id for option_id, _ in options]
        assert [o["displayOrder"] for o in item["answerOptions"]] == list(range(1, len(options) + 1))
    assert len(types) == 2  # scenario and Likert, both checked


def test_c_option_order_is_stable_and_is_the_stored_one(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    first = questions(api, headers, attempt["id"])
    assert questions(api, headers, attempt["id"]) == first
    stored = {
        row.question_id: row.option_order
        for row in db_session.scalars(
            select(Response).where(Response.test_attempt_id == uuid.UUID(attempt["id"]))
        )
    }
    for item in first:
        assert [uuid.UUID(o["id"]) for o in item["answerOptions"]] == stored[uuid.UUID(item["id"])]


def test_c_items_follow_the_cut_plan_and_alternate_the_four_systems(api, app, person, db_session):
    """On the real bank: the plan's serving order, round-robin across systems, never in blocks."""
    load_real_bank(db_session)
    _, headers = person
    bank = _bank_rows(db_session)
    served = questions(api, headers, start(api, headers)["id"])
    assert [bank[uuid.UUID(item["id"])][2] for item in served] == list(
        app.extensions["cut_plan"].cuts[0].new_item_orders
    )
    systems = [bank[uuid.UUID(item["id"])][0] for item in served]
    for start_at in range(0, len(systems), 4):
        assert len(set(systems[start_at:start_at + 4])) == 4, systems[start_at:start_at + 4]


def test_c_the_stored_answer_is_the_option_id_and_nothing_about_its_group(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)
    items = questions(api, headers, attempt["id"])
    answer_all(api, headers, attempt["id"], items[:3])
    columns = set(Response.__table__.columns.keys())
    assert not {"group_label", "grouping_system", "group"} & columns


# --- the guard itself ---------------------------------------------------------------------------


class LeakyAnswerOptionOut(AnswerOptionOut):
    """A serializer that leaks on purpose: the real one plus the answer key."""

    group_label: str


class LeakyCamelOnlyOut(AnswerOptionOut):
    grouping_system: str


def _leaky_app(payload_factory) -> Flask:
    app = Flask("leaky")

    @app.get("/leak")
    def leak():
        return jsonify(payload_factory())

    return app


@pytest.fixture()
def served_option(api, person, db_session):
    """A real option of a real attempt, with its group read from the database."""
    _, headers = person
    item = questions(api, headers, start(api, headers)["id"])[0]
    option = item["answerOptions"][0]
    row = db_session.get(AnswerOption, uuid.UUID(option["id"]))
    question = db_session.get(Question, row.question_id)
    return option, row.group_label, question.grouping_system.value


def test_the_guard_catches_a_serializer_that_leaks_the_group(served_option):
    option, group, _ = served_option
    leaky = LeakyAnswerOptionOut(**{**option, "groupLabel": group})
    client = _leaky_app(lambda: [leaky.model_dump(mode="json", by_alias=True)]).test_client()
    with pytest.raises(leak_guard.AnswerKeyLeak, match="groupLabel"):
        client.get("/leak")


def test_the_guard_catches_a_leaked_system_in_snake_case(served_option):
    option, _, system = served_option
    leaky = LeakyCamelOnlyOut(**{**option, "groupingSystem": system})
    client = _leaky_app(lambda: {"items": [leaky.model_dump(mode="json")]}).test_client()
    with pytest.raises(leak_guard.AnswerKeyLeak, match="grouping_system"):
        client.get("/leak")


def test_the_guard_catches_a_group_smuggled_as_a_value(served_option):
    option, group, _ = served_option
    client = _leaky_app(lambda: {**option, "optionText": f"Opción del grupo {group}"}).test_client()
    with pytest.raises(leak_guard.AnswerKeyLeak, match=group):
        client.get("/leak")


class LeakyResultOut(ResultOut):
    """The real result plus what is stored and never exposed."""

    model_config = {**ResultOut.model_config, "protected_namespaces": ()}

    confidence_margin: float
    model_version: str


@pytest.mark.parametrize("by_alias", [True, False], ids=["camelCase", "snake_case"])
def test_the_guard_catches_a_result_that_leaks_the_classifier_output(api, person, by_alias):
    _, headers = person
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))
    api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    result = api.get(f"/api/attempts/{attempt['id']}/result", headers=headers).get_json()
    leaky = LeakyResultOut(**result, confidenceMargin=0.42, modelVersion="otro-1")
    client = _leaky_app(lambda: leaky.model_dump(mode="json", by_alias=by_alias)).test_client()
    with pytest.raises(leak_guard.AnswerKeyLeak, match="confidence") as caught:
        client.get("/leak")
    assert "odel" in str(caught.value)  # modelVersion / model_version, flagged too


def test_the_guard_counts_what_it_checks(api, person):
    before = leak_guard.stats.json_responses
    _, headers = person
    api.get("/api/attempts", headers=headers)
    assert leak_guard.stats.json_responses == before + 1


@pytest.mark.parametrize(
    "payload",
    [
        {"group_label": "x"},
        {"GroupLabel": "x"},
        {"a": [{"b": {"groupingSystem": "x"}}]},
        {"predicted_group": "x"},
        {"predictedGroup": "x"},
        {"confidence_margin": 0.3},
        {"confidenceMargin": 0.3},
        {"model_version": "x"},
        {"modelVersion": "stub"},
        {"probabilities": {}},
        {"Probabilities": {}},
        {"confidence": "alta"},
        {"marginPct": 12},
        {"result": {"probability": 0.8}},
        {"note": "stub-tally-1"},
        {"note": "Calculado con legacy-tree-1"},
        {"text": "heart"},
        {"text": "Tu centro es HEAD."},
        {"text": "intelligence_centers"},
        {"text": "grupo positive_outlook"},
        {"gut": 3},
        ["object_relations"],
    ],
)
def test_find_leaks_flags(payload):
    assert leak_guard.find_leaks(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"optionText": "[RELLENO] Opción A del ítem 001."},
        {"text": "gutural, headers, hearth, competencyless"},
        {"accessToken": "eyJ.abc_gut-x.y"},
        {"questionType": "scenario", "status": "in_progress", "tier": "free_reduced"},
        None,
        [],
    ],
)
def test_find_leaks_leaves_clean_payloads_alone(payload):
    assert leak_guard.find_leaks(payload) == []
