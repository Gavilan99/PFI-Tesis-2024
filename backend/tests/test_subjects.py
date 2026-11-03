"""Evaluados (Feature 20): a salud/rrhh account administering the test to someone else, from its
own account, instead of taking it themselves.

Covers: registration now requires `accountType`; GET /api/subjects and DELETE /api/subjects/<id>,
salud/rrhh only; `CreateAttemptIn.subject` (account type, consent, reuse by label); abandonment and
continuation scoped per person (the account itself, or a named evaluado) rather than per account;
personalization built from the attempt's own declared context instead of the professional's
profile; and deleting a subject. The accountType lock on PATCH /api/users/me is in
tests/test_profile.py.
"""

import uuid

import pytest
from sqlalchemy import select

from app.db.models import Subject, TestAttempt
from app.db.models.enums import AttemptTier
from app.repositories import attempt_repository
from tests.attempt_helpers import answer_all, questions, start, subject_body
from tests.auth_helpers import assert_error, register_body, registered
from tests.cut_helpers import give_paid_tier


@pytest.fixture()
def professional(api, question_bank):
    user, headers = registered(api, username="Profesional")
    assert api.patch("/api/users/me", headers=headers, json={"accountType": "salud"}).status_code == 200
    return user, headers


def _closed(api, headers, **start_kwargs) -> dict:
    attempt = start(api, headers, **start_kwargs)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))
    response = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert response.status_code == 200, response.get_json()
    return attempt


def _give_attempt_the_paid_tier(db_session, attempt_id: str) -> None:
    """Like tests/test_personalized_descriptions.py's own helper: an attempt starts free_reduced
    regardless of the account's subscription (it only becomes paid by continuing past cut 1), so
    personalization tests that don't walk the cuts set it directly."""
    attempt = db_session.get(TestAttempt, uuid.UUID(attempt_id))
    attempt_repository.set_tier(db_session, attempt, AttemptTier.PAID_FULL)
    db_session.commit()


# --- registration now requires accountType --------------------------------------------------------


def test_registration_without_account_type_is_a_validation_error(api):
    body = register_body()
    del body["accountType"]
    assert_error(api.post("/api/auth/register", json=body), 400, "VALIDATION_ERROR")


@pytest.mark.parametrize("account_type", ["individual", "salud", "rrhh"])
def test_registration_accepts_every_account_type(api, account_type):
    response = api.post("/api/auth/register", json=register_body(account_type=account_type))
    assert response.status_code == 201, response.get_json()
    assert response.get_json()["user"]["accountType"] == account_type


# --- the subjects routes and creating an attempt with a subject are salud/rrhh only ---------------


def test_subjects_routes_require_authentication(api, question_bank):
    assert_error(api.get("/api/subjects"), 401, "UNAUTHORIZED")
    assert_error(api.delete(f"/api/subjects/{uuid.uuid4()}"), 401, "UNAUTHORIZED")


def test_an_individual_account_cannot_list_or_delete_subjects(api, question_bank):
    _, headers = registered(api)
    assert_error(api.get("/api/subjects", headers=headers), 403, "SUBJECTS_NOT_ALLOWED")
    assert_error(api.delete(f"/api/subjects/{uuid.uuid4()}", headers=headers), 403, "SUBJECTS_NOT_ALLOWED")


def test_an_individual_account_cannot_create_an_attempt_with_a_subject(api, question_bank):
    _, headers = registered(api)
    response = api.post("/api/attempts", headers=headers, json={"subject": subject_body("Alguien")})
    assert_error(response, 403, "SUBJECTS_NOT_ALLOWED")
    assert api.get("/api/attempts", headers=headers).get_json() == []


# --- consent is declared per test ------------------------------------------------------------------


def test_starting_a_subjects_attempt_without_consent_declared_is_rejected(api, professional):
    _, headers = professional
    response = api.post("/api/attempts", headers=headers, json={"subject": subject_body("Alguien", consent_declared=False)})
    assert_error(response, 422, "SUBJECT_CONSENT_REQUIRED")
    assert api.get("/api/subjects", headers=headers).get_json() == []


def test_starting_a_subjects_attempt_without_the_field_at_all_is_rejected(api, professional):
    _, headers = professional
    response = api.post("/api/attempts", headers=headers, json={"subject": {"label": "Alguien", "context": None}})
    assert_error(response, 422, "SUBJECT_CONSENT_REQUIRED")


# --- creating and reusing a subject by label --------------------------------------------------------


def test_starting_an_attempt_with_a_new_label_creates_the_subject(api, professional):
    _, headers = professional
    attempt = start(api, headers, subject=subject_body("Paciente Uno", context="Contexto inicial"))

    assert attempt["subjectLabel"] == "Paciente Uno"
    assert attempt["subjectContext"] == "Contexto inicial"
    assert attempt["userId"] is not None
    subjects = api.get("/api/subjects", headers=headers).get_json()
    assert [s["label"] for s in subjects] == ["Paciente Uno"]
    assert subjects[0]["testCount"] == 1
    assert subjects[0]["lastTestContext"] == "Contexto inicial"


def test_the_same_label_with_different_capitalization_reuses_the_subject(api, professional):
    _, headers = professional
    first = _closed(api, headers, subject=subject_body("Paciente Dos"))

    second = start(api, headers, subject=subject_body("PACIENTE DOS", context="Nuevo contexto"))

    assert second["subjectId"] == first["subjectId"]
    subjects = api.get("/api/subjects", headers=headers).get_json()
    assert len(subjects) == 1
    assert subjects[0]["testCount"] == 2
    assert subjects[0]["lastTestContext"] == "Nuevo contexto"


def test_two_professionals_with_the_same_label_get_different_subjects(api, question_bank):
    _, headers_a = registered(api, username="Profesional A")
    api.patch("/api/users/me", headers=headers_a, json={"accountType": "salud"})
    _, headers_b = registered(api, username="Profesional B")
    api.patch("/api/users/me", headers=headers_b, json={"accountType": "rrhh"})

    a = start(api, headers_a, subject=subject_body("Mismo nombre"))
    b = start(api, headers_b, subject=subject_body("Mismo nombre"))

    assert a["subjectId"] != b["subjectId"]
    assert len(api.get("/api/subjects", headers=headers_a).get_json()) == 1
    assert len(api.get("/api/subjects", headers=headers_b).get_json()) == 1


# --- abandonment is scoped per person, not per account ---------------------------------------------


def test_starting_a_subjects_attempt_does_not_abandon_the_professionals_own(api, professional):
    _, headers = professional
    own = start(api, headers)

    start(api, headers, subject=subject_body("Paciente"))

    assert api.get(f"/api/attempts/{own['id']}", headers=headers).get_json()["status"] == "in_progress"


def test_starting_a_second_subjects_attempt_does_not_abandon_a_different_subjects(api, professional):
    _, headers = professional
    first = start(api, headers, subject=subject_body("Sujeto A"))

    start(api, headers, subject=subject_body("Sujeto B"))

    assert api.get(f"/api/attempts/{first['id']}", headers=headers).get_json()["status"] == "in_progress"


def test_starting_the_same_subjects_attempt_again_abandons_the_previous_one(api, professional):
    _, headers = professional
    first = start(api, headers, subject=subject_body("Sujeto"))

    start(api, headers, subject=subject_body("sujeto"))

    assert api.get(f"/api/attempts/{first['id']}", headers=headers).get_json()["status"] == "abandoned"


# --- continuation is tracked per person too ---------------------------------------------------------


def test_continuation_is_tracked_per_person(api, professional, db_session):
    user, headers = professional
    give_paid_tier(db_session, user["id"])
    own = _closed(api, headers)

    subject_attempt = _closed(api, headers, subject=subject_body("Sujeto continuo"))

    # The professional's own completed attempt must not block continuing the subject's (both are
    # closed, so continuing either opens a new, linked attempt: 201).
    response = api.post(f"/api/attempts/{subject_attempt['id']}/continue", headers=headers)
    assert response.status_code == 201, response.get_json()
    assert response.get_json()["subjectId"] == subject_attempt["subjectId"]
    # And the other way around.
    response = api.post(f"/api/attempts/{own['id']}/continue", headers=headers)
    assert response.status_code == 201, response.get_json()


# --- personalization uses the attempt's own context, never the professional's profile ---------------


def test_personalization_of_a_subjects_attempt_uses_the_attempts_context(api, professional, db_session, text_generator):
    _, headers = professional
    api.patch("/api/users/me", headers=headers, json={"ageRange": "35-44", "professionContext": "Perfil del profesional"})
    attempt = _closed(api, headers, subject=subject_body("Sujeto personalización", context="Contexto del sujeto"))
    _give_attempt_the_paid_tier(db_session, attempt["id"])

    response = api.get(f"/api/attempts/{attempt['id']}/result/personalized", headers=headers)
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["status"] == "personalized"
    whole = " ".join([*body["strengths"], *body["tensions"], body["growth"], body["stress"]]).lower()
    assert "sujeto personalización" not in whole
    assert "perfil del profesional" not in whole


def test_personalization_of_a_subjects_attempt_without_context_is_context_missing(api, professional, db_session):
    _, headers = professional
    attempt = _closed(api, headers, subject=subject_body("Sujeto sin contexto"))
    _give_attempt_the_paid_tier(db_session, attempt["id"])

    response = api.get(f"/api/attempts/{attempt['id']}/result/personalized", headers=headers)
    assert response.status_code == 200, response.get_json()
    assert response.get_json() == {
        "status": "context_missing", "strengths": None, "tensions": None, "growth": None, "stress": None,
    }


# --- DELETE /api/subjects/<id> ----------------------------------------------------------------------


def test_deleting_a_subject_anonymizes_it_and_keeps_the_attempt_and_its_result(api, professional, db_session):
    _, headers = professional
    attempt = _closed(api, headers, subject=subject_body("Para borrar", context="Algo"))
    subject_id = api.get("/api/subjects", headers=headers).get_json()[0]["id"]

    response = api.delete(f"/api/subjects/{subject_id}", headers=headers)

    assert response.status_code == 204
    assert api.get("/api/subjects", headers=headers).get_json() == []
    reloaded = api.get(f"/api/attempts/{attempt['id']}", headers=headers).get_json()
    assert reloaded["subjectLabel"] is None
    assert reloaded["subjectContext"] is None
    assert api.get(f"/api/attempts/{attempt['id']}/result", headers=headers).status_code == 200

    db_session.expire_all()
    row = db_session.get(Subject, uuid.UUID(subject_id))
    assert row.label is None and row.context_data is None and row.deleted_at is not None


def test_a_deleted_labels_can_be_reused(api, professional):
    _, headers = professional
    attempt = start(api, headers, subject=subject_body("Para reusar"))
    subject_id = attempt["subjectId"]
    assert api.delete(f"/api/subjects/{subject_id}", headers=headers).status_code == 204

    again = start(api, headers, subject=subject_body("Para reusar"))

    assert again["subjectId"] != subject_id


def test_deleting_someone_elses_or_a_nonexistent_subject_is_the_same_404(api, professional, question_bank):
    _, headers = professional
    _, other_headers = registered(api, username="Otro profesional")
    api.patch("/api/users/me", headers=other_headers, json={"accountType": "rrhh"})
    theirs = start(api, other_headers, subject=subject_body("Ajeno"))

    assert_error(api.delete(f"/api/subjects/{theirs['subjectId']}", headers=headers), 404, "SUBJECT_NOT_FOUND")
    assert_error(api.delete(f"/api/subjects/{uuid.uuid4()}", headers=headers), 404, "SUBJECT_NOT_FOUND")


# --- account deletion also nulls the declared context of the account's own subject attempts --------


def test_deleting_the_account_nulls_subject_context_of_its_attempts(api, professional, db_session):
    _, headers = professional
    attempt = start(api, headers, subject=subject_body("Para borrado de cuenta", context="Contexto sensible"))

    assert api.delete("/api/users/me", headers=headers).status_code == 204

    db_session.expire_all()
    row = db_session.scalar(select(TestAttempt).where(TestAttempt.id == uuid.UUID(attempt["id"])))
    assert row.subject_context is None
