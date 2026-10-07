"""The instrument's answer key never leaves the server. Three layers, each with its own tests, plus the
tests that prove the suite-wide guard (tests/leak_guard.py) fails when something leaks.

(a) Keys: `group_label` and `grouping_system` are in no response, in any casing.
(b) Values: no group label or system name of the canonical vocabulary is in any response.
(c) Order: scenario options are shuffled per attempt (stable within it), Likert options never are,
    and the subset is served shuffled, so no position gives away a group or a system.

Layer (c) is tested against a worst-case bank, too: every scenario item lists its groups in the same
order and the bank is sorted by system. The filler is already shuffled, so on its own it would hide a
missing shuffle.
"""

import dataclasses
import uuid
from collections import Counter

import pytest
from flask import Flask, jsonify
from sqlalchemy import select

from app.blueprints.attempts.schemas import AnswerOptionOut, QuestionOut
from app.db.models import AnswerOption, Question, Response
from app.db.models.enums import GROUP_LABELS, GROUPS_BY_SYSTEM, AttemptTier, GroupingSystem, QuestionType
from app.services import attempts as attempts_service
from app.services.question_bank import load_bank
from scripts.seed_filler_bank import build_filler_bank
from tests import leak_guard
from tests.attempt_helpers import OPTION_FIELDS, QUESTION_FIELDS, answer, answer_all, questions, start
from tests.auth_helpers import registered

SYSTEM_NAMES = {system.value for system in GroupingSystem}
FORBIDDEN_KEY_SPELLINGS = ("group_label", "groupLabel", "grouping_system", "groupingSystem")


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


@pytest.fixture()
def paid_full(monkeypatch):
    """60 items per attempt: more items per request, fewer requests per statistic."""
    monkeypatch.setattr(attempts_service, "resolve_attempt_tier", lambda user: AttemptTier.PAID_FULL)


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
        api.post(f"/api/attempts/{attempt_id}/complete", headers=headers),
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


def _worst_case_bank():
    """The filler, rearranged the way a careless CSV could come: scenario options always in the
    vocabulary's group order, and questions sorted by system."""
    bank = []
    for question in build_filler_bank():
        options = question.options
        if question.question_type is QuestionType.SCENARIO:
            rank = GROUPS_BY_SYSTEM[question.grouping_system].index
            options = tuple(
                dataclasses.replace(o, display_order=k)
                for k, o in enumerate(sorted(options, key=lambda o: rank(o.group_label)), start=1)
            )
        bank.append(dataclasses.replace(question, options=options))
    systems = list(GroupingSystem)
    bank.sort(key=lambda q: (systems.index(q.grouping_system), q.display_order))
    return [dataclasses.replace(q, display_order=k) for k, q in enumerate(bank, start=1)]


@pytest.fixture()
def worst_case_bank(db_session):
    load_bank(db_session, _worst_case_bank(), version=1, activate=True)
    db_session.commit()


# --- (a) keys -----------------------------------------------------------------------------------


def test_a_the_output_schemas_have_exactly_the_contract_fields():
    assert {f.alias for f in QuestionOut.model_fields.values()} == QUESTION_FIELDS
    assert {f.alias for f in AnswerOptionOut.model_fields.values()} == OPTION_FIELDS


def test_a_no_response_carries_the_answer_key_fields(api, person):
    _, headers = person
    for response in _every_attempt_response(api, headers):
        body = response.get_data(as_text=True)
        for spelling in FORBIDDEN_KEY_SPELLINGS:
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


def test_c_scenario_options_are_shuffled_per_attempt(api, person, db_session, paid_full, worst_case_bank):
    """Against a bank where the position *is* the group, each position must carry every group."""
    _, headers = person
    bank = _bank_rows(db_session)
    by_position: dict[int, Counter] = {1: Counter(), 2: Counter(), 3: Counter()}
    for _ in range(15):
        for item in questions(api, headers, start(api, headers)["id"]):
            system, question_type, _, options = bank[uuid.UUID(item["id"])]
            if question_type is not QuestionType.SCENARIO:
                continue
            group = dict(options)
            for option in item["answerOptions"]:
                rank = GROUPS_BY_SYSTEM[system].index(group[uuid.UUID(option["id"])])
                by_position[option["displayOrder"]][rank] += 1

    for position, ranks in by_position.items():
        total = sum(ranks.values())
        assert total > 500
        shares = {rank: count / total for rank, count in ranks.items()}
        # Uniform is 1/3 each. Without the shuffle, one rank would hold 100% of its position.
        assert set(shares) == {0, 1, 2}, (position, shares)
        assert all(0.25 < share < 0.42 for share in shares.values()), (position, shares)


def test_c_scenario_option_order_is_stable_within_an_attempt_and_is_the_stored_one(api, person, db_session):
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


def test_c_scenario_option_order_changes_between_attempts(api, person, db_session, paid_full):
    _, headers = person
    bank = _bank_rows(db_session)
    permutations: Counter = Counter()
    same_as_bank = scenario_items = 0
    for _ in range(10):
        for item in questions(api, headers, start(api, headers)["id"]):
            _, question_type, _, options = bank[uuid.UUID(item["id"])]
            if question_type is not QuestionType.SCENARIO:
                continue
            served = [uuid.UUID(o["id"]) for o in item["answerOptions"]]
            bank_ids = [option_id for option_id, _ in options]
            permutations[tuple(bank_ids.index(i) for i in served)] += 1
            scenario_items += 1
            same_as_bank += served == bank_ids
    assert len(permutations) == 6
    assert 0.08 < same_as_bank / scenario_items < 0.28  # 1/6 expected


def test_c_likert_options_are_never_shuffled(api, person, db_session, paid_full, worst_case_bank):
    _, headers = person
    bank = _bank_rows(db_session)
    likert_items = 0
    for _ in range(10):
        for item in questions(api, headers, start(api, headers)["id"]):
            _, question_type, _, options = bank[uuid.UUID(item["id"])]
            if question_type is not QuestionType.MULTIPLE_CHOICE:
                continue
            likert_items += 1
            served = [uuid.UUID(o["id"]) for o in item["answerOptions"]]
            assert served == [option_id for option_id, _ in options]
            assert [o["displayOrder"] for o in item["answerOptions"]] == [1, 2, 3, 4, 5]
    assert likert_items > 50


def test_c_questions_are_served_shuffled(api, person, db_session, paid_full, worst_case_bank):
    """Against a bank sorted by system, the served position must not give the system away."""
    _, headers = person
    bank = _bank_rows(db_session)
    first_systems: Counter = Counter()
    for _ in range(12):
        served = questions(api, headers, start(api, headers)["id"])
        bank_orders = [bank[uuid.UUID(item["id"])][2] for item in served]
        assert bank_orders != sorted(bank_orders)
        systems = [bank[uuid.UUID(item["id"])][0] for item in served]
        # In a sorted serve, the first 15 items would all be one system.
        assert len(set(systems[:15])) > 1
        first_systems[systems[0]] += 1
    assert len(first_systems) > 1


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
        {"confidenceMargin": 0.3},
        {"modelVersion": "stub"},
        {"probabilities": {}},
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
