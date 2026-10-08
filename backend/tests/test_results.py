"""Results end to end (RF04, RF05, RF08, CU004): closing an attempt classifies it and stores the
result, `GET /api/attempts/{id}/result` reads it, and what is internal stays in the database.

Runs against the filler bank, version 0, with `CLASSIFIER_BACKEND=stub` unless a test builds an app
with another backend.
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.db.models import ClassifierPrediction, Result, TestAttempt
from app.db.models.enums import AttemptStatus
from app.ml import registry
from app.ml.classification import Classification, SystemPrediction
from app.ml.config import TAXONOMIES, TYPE_TABLE
from app.ml.legacy.tree import LEGACY_MODEL_VERSION
from app.ml.stub import STUB_MODEL_VERSION, StubClassifier
from app.repositories import result_repository
from app.services.result_descriptions import PROVISIONAL_DESCRIPTIONS
from tests.attempt_helpers import answer_all, questions, start
from tests.auth_helpers import assert_error, registered
from tests.classifier_helpers import app_with_backend, complete_as_type

RESULT_FIELDS = {"id", "testAttemptId", "eneatype", "descriptionText", "generatedAt"}


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


def _closed(api, headers) -> dict:
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))
    response = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert response.status_code == 200, response.get_json()
    return attempt


def _result(api, headers, attempt_id) -> dict:
    response = api.get(f"/api/attempts/{attempt_id}/result", headers=headers)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def _rows(session, attempt_id) -> tuple[list[ClassifierPrediction], list[Result]]:
    session.expire_all()
    attempt_id = uuid.UUID(str(attempt_id))
    predictions = session.scalars(
        select(ClassifierPrediction).where(ClassifierPrediction.test_attempt_id == attempt_id)
    ).all()
    results = session.scalars(select(Result).where(Result.test_attempt_id == attempt_id)).all()
    return list(predictions), list(results)


# --- closing stores the result ------------------------------------------------------------------


def test_closing_stores_four_predictions_and_one_result(api, person, db_session):
    _, headers = person
    attempt = _closed(api, headers)
    predictions, results = _rows(db_session, attempt["id"])

    assert {p.grouping_system.value for p in predictions} == set(TAXONOMIES)
    for prediction in predictions:
        groups = TAXONOMIES[prediction.grouping_system.value]
        assert set(prediction.probabilities) == set(groups)
        assert sum(prediction.probabilities.values()) == pytest.approx(1)
        assert prediction.predicted_group in groups
        assert prediction.model_version == STUB_MODEL_VERSION
    [result] = results
    assert 1 <= result.eneatype <= 9
    assert result.confidence_margin is not None and result.confidence_margin >= 0
    assert result.description_text == PROVISIONAL_DESCRIPTIONS[result.eneatype]
    # Dated at its insert, inside the close: never before the attempt's completed_at.
    assert result.generated_at >= db_session.get(TestAttempt, uuid.UUID(attempt["id"])).completed_at


def test_the_stored_result_is_the_stub_classification_of_the_stored_answers(api, person, db_session):
    _, headers = person
    attempt = _closed(api, headers)
    expected = StubClassifier().classify(
        result_repository.classification_inputs(db_session, uuid.UUID(attempt["id"]))
    )
    predictions, [result] = _rows(db_session, attempt["id"])
    assert result.eneatype == expected.eneatype
    assert float(result.confidence_margin) == pytest.approx(expected.confidence_margin)
    for prediction in predictions:
        stub = expected.systems[prediction.grouping_system.value]
        assert prediction.predicted_group == stub.predicted_group
        assert prediction.probabilities == pytest.approx(stub.probabilities)


@pytest.mark.parametrize("eneatype", TYPE_TABLE)
def test_every_eneatype_is_reachable_with_answers_chosen_for_it(api, person, db_session, eneatype):
    _, headers = person
    attempt = complete_as_type(api, headers, db_session, eneatype)
    result = _result(api, headers, attempt["id"])
    assert result["eneatype"] == eneatype
    assert result["descriptionText"] == PROVISIONAL_DESCRIPTIONS[eneatype]


# --- GET /api/attempts/{id}/result --------------------------------------------------------------


def test_the_result_has_exactly_the_contract_fields(api, person, db_session):
    _, headers = person
    attempt = _closed(api, headers)
    result = _result(api, headers, attempt["id"])
    assert set(result) == RESULT_FIELDS
    _, [row] = _rows(db_session, attempt["id"])
    assert result["id"] == str(row.id)
    assert result["testAttemptId"] == attempt["id"]
    assert result["eneatype"] == row.eneatype
    assert result["descriptionText"] == row.description_text
    assert result["generatedAt"]


def test_nothing_about_the_margin_reaches_the_client(api, person, db_session):
    """Two results of the same type with different margins look exactly alike, apart from ids and
    dates: nothing in the response varies with the margin."""
    _, headers = person
    first = complete_as_type(api, headers, db_session, 7)
    second = _closed(api, headers)
    db_session.execute(
        Result.__table__.update()
        .where(Result.test_attempt_id == uuid.UUID(second["id"]))
        .values(eneatype=7, description_text=PROVISIONAL_DESCRIPTIONS[7], confidence_margin=0)
    )
    db_session.commit()
    a, b = _result(api, headers, first["id"]), _result(api, headers, second["id"])
    _, [row_a] = _rows(db_session, first["id"])
    assert row_a.confidence_margin != 0
    strip = lambda r: {k: v for k, v in r.items() if k not in ("id", "testAttemptId", "generatedAt")}  # noqa: E731
    assert strip(a) == strip(b)


def test_an_attempt_in_progress_has_no_result(api, person):
    _, headers = person
    attempt = start(api, headers)
    response = api.get(f"/api/attempts/{attempt['id']}/result", headers=headers)
    assert_error(response, 404, "RESULT_NOT_FOUND", "El resultado no existe.")


def test_an_abandoned_attempt_has_no_result(api, person):
    _, headers = person
    old = start(api, headers)
    start(api, headers)
    assert_error(api.get(f"/api/attempts/{old['id']}/result", headers=headers), 404, "RESULT_NOT_FOUND")


def test_someone_elses_result_is_the_same_404_as_none(api, person):
    _, owner = person
    attempt = _closed(api, owner)
    _, intruder = registered(api)
    foreign = api.get(f"/api/attempts/{attempt['id']}/result", headers=intruder)
    missing = api.get(f"/api/attempts/{uuid.uuid4()}/result", headers=intruder)
    assert_error(foreign, 404, "RESULT_NOT_FOUND")
    assert foreign.get_json() == missing.get_json()


def test_the_result_requires_authentication(api, question_bank):
    assert_error(api.get(f"/api/attempts/{uuid.uuid4()}/result"), 401, "UNAUTHORIZED")


def test_a_malformed_id_is_404(api, person):
    _, headers = person
    assert_error(api.get("/api/attempts/no-es-un-uuid/result", headers=headers), 404, "NOT_FOUND")


# --- history is preserved -----------------------------------------------------------------------


class _Fixed:
    """A backend that always answers the same eneatype, to see whether anything gets recomputed."""

    def __init__(self, eneatype: int, model_version: str = "fixed-test-1") -> None:
        self.eneatype = eneatype
        self.model_version = model_version
        self.calls = 0

    def classify(self, answers) -> Classification:
        self.calls += 1
        groups = TYPE_TABLE[self.eneatype]
        return Classification(
            systems={
                system: SystemPrediction(
                    system, groups[system], {g: 1.0 if g == groups[system] else 0.0 for g in TAXONOMIES[system]}
                )
                for system in TAXONOMIES
            },
            eneatype=self.eneatype,
            confidence_margin=0.5,
            model_version=self.model_version,
        )


def test_closing_twice_neither_recomputes_nor_overwrites(api, app, person, db_session, monkeypatch):
    _, headers = person
    attempt = _closed(api, headers)
    before = _result(api, headers, attempt["id"])
    predictions_before, _ = _rows(db_session, attempt["id"])

    # Even with another backend in place, the second close must not classify again.
    other = _Fixed(eneatype=before["eneatype"] % 9 + 1)
    monkeypatch.setitem(app.extensions, "classifier", other)
    assert api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers).status_code == 200

    assert other.calls == 0
    assert _result(api, headers, attempt["id"]) == before
    predictions_after, results_after = _rows(db_session, attempt["id"])
    assert len(results_after) == 1
    assert [(p.id, p.model_version, p.probabilities) for p in predictions_after] == [
        (p.id, p.model_version, p.probabilities) for p in predictions_before
    ]


def test_every_closed_attempt_keeps_its_own_result(api, person, db_session):
    _, headers = person
    attempts = [complete_as_type(api, headers, db_session, eneatype) for eneatype in (3, 8)]
    assert [_result(api, headers, a["id"])["eneatype"] for a in attempts] == [3, 8]
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Result)) == 2
    assert db_session.scalar(select(func.count()).select_from(ClassifierPrediction)) == 8


# --- a failing classification leaves the attempt open -------------------------------------------


class _Broken:
    model_version = "broken-test-1"

    def classify(self, answers):
        raise RuntimeError("model exploded")


class _Malformed(_Fixed):
    def classify(self, answers):
        return Classification(systems={}, eneatype=12, confidence_margin=-1, model_version=self.model_version)


@pytest.mark.parametrize("backend", [_Broken(), _Malformed(eneatype=1)], ids=["raises", "malformed"])
def test_a_failed_classification_does_not_close_the_attempt(api, app, person, db_session, monkeypatch, backend):
    _, headers = person
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))

    monkeypatch.setitem(app.extensions, "classifier", backend)
    response = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert_error(response, 500, "RESULT_NOT_GENERATED")

    db_session.expire_all()
    row = db_session.get(TestAttempt, uuid.UUID(attempt["id"]))
    assert row.status is AttemptStatus.IN_PROGRESS and row.completed_at is None
    assert _rows(db_session, attempt["id"]) == ([], [])

    # Once the classifier works, the same attempt closes normally.
    monkeypatch.setitem(app.extensions, "classifier", StubClassifier())
    assert api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers).status_code == 200
    assert _result(api, headers, attempt["id"])


# --- the seam: a backend enters by configuration ------------------------------------------------


def test_a_new_backend_enters_by_configuration_without_touching_routes_or_services(
    app, migrated_database, monkeypatch
):
    """A fake implementation registered here, chosen with CLASSIFIER_BACKEND, closes an attempt through
    the unchanged routes and services; its output is what gets stored."""
    fake = _Fixed(eneatype=6, model_version="fake-from-test-1")
    registry.register("fake_from_test", lambda config: fake)
    try:
        with app_with_backend(app, monkeypatch, "fake_from_test") as (fake_app, session):
            assert fake_app.extensions["classifier"] is fake
            client = fake_app.test_client()
            _, headers = registered(client)
            attempt = _closed(client, headers)

            assert fake.calls == 1
            assert _result(client, headers, attempt["id"])["eneatype"] == 6
            predictions, [result] = _rows(session, attempt["id"])
            assert {p.model_version for p in predictions} == {"fake-from-test-1"}
            assert result.eneatype == 6
    finally:
        registry.unregister("fake_from_test")


def _routes(flask_app) -> set:
    return {(rule.rule, rule.endpoint, tuple(sorted(rule.methods))) for rule in flask_app.url_map.iter_rules()}


def test_switching_between_stub_and_legacy_tree_touches_no_route(app, migrated_database, monkeypatch):
    """The same requests through the same routes, with each backend: each stores its own version."""
    seen = {}
    for backend, version in (("stub", STUB_MODEL_VERSION), ("legacy_tree", LEGACY_MODEL_VERSION)):
        with app_with_backend(app, monkeypatch, backend) as (other, session):
            client = other.test_client()
            _, headers = registered(client)
            attempt = _closed(client, headers)
            result = _result(client, headers, attempt["id"])
            predictions, [row] = _rows(session, attempt["id"])

            assert set(result) == RESULT_FIELDS
            assert 1 <= result["eneatype"] <= 9
            assert {p.model_version for p in predictions} == {version}
            assert row.eneatype == result["eneatype"]
            seen[backend] = (_routes(other), {name: view.__code__ for name, view in other.view_functions.items()})

    assert seen["stub"] == seen["legacy_tree"]
    assert seen["stub"][0] == _routes(app)
