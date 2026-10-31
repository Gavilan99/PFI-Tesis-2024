"""GET /api/attempts/{id}/result/personalized (Feature 17): a personalized version of the result
screen's four sections (strengths, tensions, growth, stress), generated once per profile and model,
with none of the classifier's internal data and none of gender, country, email or display name ever
in the prompt (RNF04).

Runs against the local text generator (`tests/conftest.py`'s `text_generator` fixture, swapped in by
`api` like identity, mail and payments). It answers in the same FORTALEZAS/TENSIONES/CRECIMIENTO/
ESTRES format Bedrock is asked for, built around a short hash of the user prompt it was given, so a
test can tell two generations apart without a real model: see app.services.text_generation.local.
"""

import uuid

import pytest
from sqlalchemy import select

from app.db.models import Result, TestAttempt
from app.db.models.enums import AttemptTier
from app.repositories import attempt_repository
from app.services import personalized_descriptions as pd
from tests.attempt_helpers import answer_all, questions, start
from tests.auth_helpers import assert_error, registered

URL = "/api/attempts/{}/result/personalized"
NOTHING = {"status": None, "strengths": None, "tensions": None, "growth": None, "stress": None}


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


def _closed(api, headers) -> dict:
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))
    response = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert response.status_code == 200, response.get_json()
    return attempt


def _give_paid_tier(db_session, attempt_id: str) -> None:
    attempt = db_session.get(TestAttempt, uuid.UUID(attempt_id))
    attempt_repository.set_tier(db_session, attempt, AttemptTier.PAID_FULL)
    db_session.commit()


def _set_profile(api, headers, **fields) -> dict:
    response = api.patch("/api/users/me", headers=headers, json=fields)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _personalized(api, headers, attempt_id) -> dict:
    response = api.get(URL.format(attempt_id), headers=headers)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _nothing(status: str) -> dict:
    return {**NOTHING, "status": status}


def _stored(db_session, attempt_id: str) -> Result:
    db_session.expire_all()
    return db_session.scalar(select(Result).where(Result.test_attempt_id == uuid.UUID(attempt_id)))


# --- access: the same rule, and the same 404, as GET .../result --------------------------------


def test_requires_authentication(api, question_bank):
    assert_error(api.get(URL.format(uuid.uuid4())), 401, "UNAUTHORIZED")


def test_someone_elses_attempt_is_the_same_404(api, person):
    _, owner = person
    attempt = _closed(api, owner)
    _, intruder = registered(api)
    response = api.get(URL.format(attempt["id"]), headers=intruder)
    assert_error(response, 404, "RESULT_NOT_FOUND")


def test_an_open_attempt_is_404(api, person):
    _, headers = person
    attempt = start(api, headers)
    assert_error(api.get(URL.format(attempt["id"]), headers=headers), 404, "RESULT_NOT_FOUND")


# --- free plan: never calls the generator -------------------------------------------------------


def test_a_free_attempt_is_not_in_plan_and_never_calls_the_generator(api, person, text_generator):
    _, headers = person
    attempt = _closed(api, headers)
    _set_profile(api, headers, accountType="individual")
    assert _personalized(api, headers, attempt["id"]) == _nothing("not_in_plan")
    assert text_generator.calls == 0


# --- paid plan, nothing in the profile ------------------------------------------------------------


def test_paid_with_an_empty_profile_is_profile_missing_and_never_calls_the_generator(
    api, person, db_session, text_generator
):
    _, headers = person
    attempt = _closed(api, headers)
    _give_paid_tier(db_session, attempt["id"])
    assert _personalized(api, headers, attempt["id"]) == _nothing("profile_missing")
    assert text_generator.calls == 0


# --- paid plan, with a profile ---------------------------------------------------------------------


def test_paid_with_one_profile_field_is_personalized(api, person, db_session, text_generator):
    _, headers = person
    attempt = _closed(api, headers)
    _give_paid_tier(db_session, attempt["id"])
    _set_profile(api, headers, accountType="individual")

    body = _personalized(api, headers, attempt["id"])

    assert body["status"] == "personalized"
    assert 3 <= len(body["strengths"]) <= 6 and all(body["strengths"])
    assert 3 <= len(body["tensions"]) <= 6 and all(body["tensions"])
    assert body["growth"] and body["stress"]
    assert text_generator.calls == 1

    row = _stored(db_session, attempt["id"])
    assert row.personalized_strengths == body["strengths"]
    assert row.personalized_tensions == body["tensions"]
    assert row.personalized_growth == body["growth"]
    assert row.personalized_stress == body["stress"]
    assert row.personalized_model == text_generator.model_id
    assert row.personalized_profile_hash
    assert row.personalized_at is not None


def test_a_second_call_with_the_same_profile_does_not_regenerate(api, person, db_session, text_generator):
    _, headers = person
    attempt = _closed(api, headers)
    _give_paid_tier(db_session, attempt["id"])
    _set_profile(api, headers, accountType="individual")

    first = _personalized(api, headers, attempt["id"])
    second = _personalized(api, headers, attempt["id"])

    assert first == second
    assert text_generator.calls == 1


def test_changing_the_profile_regenerates(api, person, db_session, text_generator):
    _, headers = person
    attempt = _closed(api, headers)
    _give_paid_tier(db_session, attempt["id"])
    _set_profile(api, headers, accountType="individual")
    first = _personalized(api, headers, attempt["id"])

    _set_profile(api, headers, ageRange="35-44")
    second = _personalized(api, headers, attempt["id"])

    assert text_generator.calls == 2
    assert first["growth"] != second["growth"]
    assert first["strengths"] != second["strengths"]


# --- failures: unavailable, nothing stored, next visit retries -------------------------------------


def test_a_failed_generation_is_unavailable_and_stores_nothing(api, person, db_session, text_generator):
    _, headers = person
    attempt = _closed(api, headers)
    _give_paid_tier(db_session, attempt["id"])
    _set_profile(api, headers, accountType="individual")

    text_generator.fail = True
    assert _personalized(api, headers, attempt["id"]) == _nothing("unavailable")
    row = _stored(db_session, attempt["id"])
    assert row.personalized_strengths is None
    assert row.personalized_tensions is None
    assert row.personalized_growth is None
    assert row.personalized_stress is None
    assert row.personalized_profile_hash is None
    assert row.personalized_model is None
    assert row.personalized_at is None

    # Nothing was kept on the failed call, so the next visit tries again instead of staying stuck.
    text_generator.fail = False
    assert _personalized(api, headers, attempt["id"])["status"] == "personalized"


@pytest.mark.parametrize(
    "broken_answer",
    [
        "esto no sigue el formato pedido en absoluto",
        "FORTALEZAS:\nuna sola\nTENSIONES:\na\nb\nc\nCRECIMIENTO:\npárrafo\nESTRES:\npárrafo",
        "FORTALEZAS:\na\nb\nc\nTENSIONES:\na\nb\nc\nCRECIMIENTO:\ncorto\nESTRES:\npárrafo largo",
    ],
    ids=["no-markers", "too-few-strengths", "growth-too-short"],
)
def test_an_answer_that_does_not_pass_validation_is_unavailable_and_stores_nothing(
    api, person, db_session, text_generator, monkeypatch, broken_answer
):
    _, headers = person
    attempt = _closed(api, headers)
    _give_paid_tier(db_session, attempt["id"])
    _set_profile(api, headers, accountType="individual")

    monkeypatch.setattr(text_generator, "generate", lambda system, user: broken_answer)
    assert _personalized(api, headers, attempt["id"]) == _nothing("unavailable")
    assert _stored(db_session, attempt["id"]).personalized_strengths is None


# --- confidentiality (RNF04): the prompt never carries what it must not ---------------------------


def test_the_prompt_never_carries_gender_country_email_or_the_display_name(
    api, person, db_session, text_generator
):
    user, headers = person
    attempt = _closed(api, headers)
    _give_paid_tier(db_session, attempt["id"])
    _set_profile(
        api, headers,
        accountType="salud", ageRange="45-54", gender="femenino", country="Argentina",
        professionContext="Enfermera en un hospital",
    )

    body = _personalized(api, headers, attempt["id"])
    assert body["status"] == "personalized"
    whole = " ".join([*body["strengths"], *body["tensions"], body["growth"], body["stress"]]).lower()
    for leaked in ("femenino", "argentina", user["email"].lower(), (user["displayName"] or "").lower()):
        assert leaked, "the value to check for a leak must not itself be empty"
        assert leaked not in whole


def test_the_professional_context_is_truncated_and_delimited():
    long_context = "x" * 400
    prompt = pd._user_prompt(7, "descripción base", None, None, long_context)

    assert f"<contexto_profesional>{'x' * 255}</contexto_profesional>" in prompt
    assert "x" * 256 not in prompt


def test_the_fingerprint_uses_the_truncated_profession_context_too():
    short = pd._fingerprint(None, None, "x" * 255, "model-1")
    long = pd._fingerprint(None, None, "x" * 255 + "y" * 50, "model-1")
    assert short == long


# --- the parser (plain string handling, not structured output) ------------------------------------


_ITEMS = "fortaleza uno\nfortaleza dos\nfortaleza tres"


def _formatted(strengths=_ITEMS, tensions=_ITEMS, growth="g" * 80, stress="s" * 80) -> str:
    return f"FORTALEZAS:\n{strengths}\nTENSIONES:\n{tensions}\nCRECIMIENTO:\n{growth}\nESTRES:\n{stress}"


def test_a_well_formed_answer_parses_into_the_four_sections():
    parsed = pd._parsed_and_valid(_formatted())
    assert parsed == (_ITEMS.split("\n"), _ITEMS.split("\n"), "g" * 80, "s" * 80)


def test_markers_out_of_order_fail_to_parse():
    assert pd._parse_sections("TENSIONES:\na\nFORTALEZAS:\na\nCRECIMIENTO:\na\nESTRES:\na") is None


def test_a_missing_marker_fails_to_parse():
    assert pd._parse_sections("FORTALEZAS:\na\nTENSIONES:\na\nESTRES:\na") is None


def test_bullet_markers_and_surrounding_blanks_are_stripped():
    parsed = pd._parse_sections(_formatted(strengths="- a\n* b\n  c  \n\n"))
    assert parsed["FORTALEZAS"] == ["a", "b", "c"]


@pytest.mark.parametrize("count", [1, 2, 7, 8])
def test_a_list_with_too_few_or_too_many_items_is_invalid(count):
    items = "\n".join(f"elemento número {i}" for i in range(count))
    assert pd._parsed_and_valid(_formatted(strengths=items)) is None


def test_an_empty_paragraph_is_invalid():
    assert pd._parsed_and_valid(_formatted(growth="")) is None


def test_a_paragraph_that_is_too_long_is_invalid():
    assert pd._parsed_and_valid(_formatted(growth="g" * 800)) is None
