"""`CLASSIFIER_BACKEND=trained` classifying real attempts: bank v4.1.2 and the session's synthetic models.

The result of an attempt comes from the four models of its last complete cut, and its predictions are
stored with that cut's model version. Anything that does not match a cut exactly is an error.
"""

import uuid

import numpy as np
import pytest
from sqlalchemy import select

from app.db.models import ClassifierPrediction, TestAttempt
from app.ml.classification import Answer
from app.ml.config import TAXONOMIES
from app.ml.training.bank import LIKERT, SCENARIO, Item
from app.ml.training.encoding import encode_one
from app.repositories.result_repository import classification_inputs
from tests.attempt_helpers import start
from tests.auth_helpers import assert_error, registered
from tests.classifier_helpers import app_with_backend
from tests.cut_helpers import answer_everything, complete, continue_, give_paid_tier


@pytest.fixture()
def trained(app, migrated_database, monkeypatch):
    with app_with_backend(app, monkeypatch, "trained", real_bank=True) as (other, session):
        yield other, other.test_client(), session


def _versions(session, attempt_id) -> set[str]:
    session.expire_all()
    return set(
        session.scalars(
            select(ClassifierPrediction.model_version).where(
                ClassifierPrediction.test_attempt_id == uuid.UUID(attempt_id)
            )
        )
    )


def _prediction_count(session, attempt_id) -> int:
    return len(
        session.scalars(
            select(ClassifierPrediction.id).where(ClassifierPrediction.test_attempt_id == uuid.UUID(attempt_id))
        ).all()
    )


def test_closing_at_cut_1_uses_the_models_of_cut_1(trained):
    other, client, session = trained
    version = other.extensions["classifier"].model_version
    _, headers = registered(client)
    attempt = start(client, headers)
    answer_everything(client, headers, attempt["id"])
    complete(client, headers, attempt["id"])
    assert _prediction_count(session, attempt["id"]) == 4
    assert _versions(session, attempt["id"]) == {f"{version}/cut_040"}
    assert client.get(f"/api/attempts/{attempt['id']}/result", headers=headers).status_code == 200


def test_closing_at_cut_2_uses_the_models_of_cut_2(trained):
    other, client, session = trained
    version = other.extensions["classifier"].model_version
    user, headers = registered(client)
    give_paid_tier(session, user["id"])
    attempt = start(client, headers)
    answer_everything(client, headers, attempt["id"])
    continue_(client, headers, attempt["id"])
    answer_everything(client, headers, attempt["id"])
    complete(client, headers, attempt["id"])
    assert _versions(session, attempt["id"]) == {f"{version}/cut_090"}
    session.expire_all()
    assert session.get(TestAttempt, uuid.UUID(attempt["id"])).tier.value == "paid_full"


def test_closing_at_cut_3_uses_the_models_of_cut_3(trained):
    other, client, session = trained
    user, headers = registered(client)
    give_paid_tier(session, user["id"])
    attempt = start(client, headers)
    for _ in range(2):
        answer_everything(client, headers, attempt["id"])
        continue_(client, headers, attempt["id"])
    answer_everything(client, headers, attempt["id"])
    complete(client, headers, attempt["id"])
    assert _versions(session, attempt["id"]) == {f"{other.extensions['classifier'].model_version}/cut_145"}


def test_a_linked_attempt_closes_with_cut_2_and_the_old_keeps_cut_1(trained):
    other, client, session = trained
    version = other.extensions["classifier"].model_version
    user, headers = registered(client)
    old = start(client, headers)
    answer_everything(client, headers, old["id"])
    complete(client, headers, old["id"])
    give_paid_tier(session, user["id"])
    new = continue_(client, headers, old["id"]).get_json()
    answer_everything(client, headers, new["id"])
    complete(client, headers, new["id"])
    assert _versions(session, old["id"]) == {f"{version}/cut_040"}
    assert _versions(session, new["id"]) == {f"{version}/cut_090"}
    assert_error(continue_(client, headers, old["id"]), 409, "ATTEMPT_ALREADY_CONTINUED")


def test_the_distributions_are_the_models_own(trained):
    """Encoded with the training's encode_one and passed through each pipeline's predict_proba."""
    other, client, session = trained
    classifier = other.extensions["classifier"]
    _, headers = registered(client)
    attempt = start(client, headers)
    answer_everything(client, headers, attempt["id"])
    answers = classification_inputs(session, uuid.UUID(attempt["id"]))
    classification = classifier.classify(answers)

    cut = classifier.plan.cuts[0]
    by_code = {f"Q{a.question_order:03d}": a for a in answers}
    items = [
        Item(code, by_code[code].question_order, by_code[code].grouping_system,
             SCENARIO if by_code[code].option_count == 3 else LIKERT, by_code[code].option_count)
        for code in cut.model_items
    ]
    row = np.asarray([encode_one({c: by_code[c].option_position for c in cut.model_items}, items)])
    for system in TAXONOMIES:
        model = classifier.models[1][system]
        expected = dict(zip(model.classes_, model.predict_proba(row)[0]))
        assert classification.systems[system].probabilities == pytest.approx(
            {g: expected[g] for g in TAXONOMIES[system]}
        )


def test_answers_that_match_no_cut_are_an_error_never_a_default(trained):
    other, client, session = trained
    classifier = other.extensions["classifier"]
    _, headers = registered(client)
    attempt = start(client, headers)
    answer_everything(client, headers, attempt["id"])
    answers = classification_inputs(session, uuid.UUID(attempt["id"]))
    with pytest.raises(ValueError, match="match no cut"):
        classifier.classify(answers[:-1])
    extra = Answer(**{**answers[0].__dict__, "question_order": 145, "question_id": uuid.uuid4()})
    with pytest.raises(ValueError, match="match no cut"):
        classifier.classify([*answers, extra])


def test_items_of_another_format_do_not_encode_to_the_cuts_columns(app, migrated_database, monkeypatch):
    """On the filler, the plan's numbers exist but are not the bank's items: closing fails, the attempt
    stays open, and nothing is stored."""
    with app_with_backend(app, monkeypatch, "trained") as (other, session):
        client = other.test_client()
        _, headers = registered(client)
        attempt = start(client, headers)
        answer_everything(client, headers, attempt["id"])
        response = client.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
        assert_error(response, 500, "RESULT_NOT_GENERATED")
        assert _prediction_count(session, attempt["id"]) == 0
        session.expire_all()
        assert session.get(TestAttempt, uuid.UUID(attempt["id"])).status.value == "in_progress"
