"""POST /api/feedback (RF06): a rating and an optional comment, from the token's user, never shown back.

Also the end of its life: deleting the account nulls the comment and keeps the rating.
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.blueprints.feedback.schemas import COMMENT_MAX_LENGTH
from app.db.models import Feedback
from tests.attempt_helpers import start
from tests.auth_helpers import assert_error, registered


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


def _body(**overrides) -> dict:
    return {"testAttemptId": None, "rating": 4, "comment": "Me sirvió.", **overrides}


def _rows(session) -> list[Feedback]:
    session.expire_all()
    return list(session.scalars(select(Feedback).order_by(Feedback.submitted_at)))


def _count(session) -> int:
    return session.scalar(select(func.count()).select_from(Feedback))


def test_general_feedback_is_stored_for_the_token_user_and_returns_nothing(api, person, db_session):
    user, headers = person

    response = api.post("/api/feedback", headers=headers, json=_body())

    assert response.status_code == 204
    assert response.get_data() == b""
    [row] = _rows(db_session)
    assert str(row.user_id) == user["id"]
    assert row.test_attempt_id is None
    assert (row.rating, row.comment) == (4, "Me sirvió.")
    assert row.submitted_at is not None


def test_feedback_tied_to_an_own_attempt(api, person, db_session):
    _, headers = person
    attempt = start(api, headers)

    response = api.post("/api/feedback", headers=headers, json=_body(testAttemptId=attempt["id"], rating=5))

    assert response.status_code == 204
    [row] = _rows(db_session)
    assert str(row.test_attempt_id) == attempt["id"]
    assert row.rating == 5


def test_a_comment_is_optional_and_blank_is_none(api, person, db_session):
    _, headers = person
    assert api.post("/api/feedback", headers=headers, json=_body(comment=None)).status_code == 204
    assert api.post("/api/feedback", headers=headers, json=_body(comment="   ")).status_code == 204
    assert [row.comment for row in _rows(db_session)] == [None, None]


@pytest.mark.parametrize("rating", [0, 6, -1, 4.5, "4", True, None])
def test_a_rating_outside_1_to_5_is_rejected(api, person, db_session, rating):
    _, headers = person
    response = api.post("/api/feedback", headers=headers, json=_body(rating=rating))
    assert_error(response, 400, "VALIDATION_ERROR", "Los datos enviados no son válidos.")
    assert _count(db_session) == 0


def test_every_rating_from_1_to_5_is_accepted(api, person, db_session):
    _, headers = person
    for rating in range(1, 6):
        assert api.post("/api/feedback", headers=headers, json=_body(rating=rating)).status_code == 204
    assert sorted(row.rating for row in _rows(db_session)) == [1, 2, 3, 4, 5]


def test_feedback_on_someone_elses_attempt_is_the_same_404_as_none(api, person, db_session):
    _, headers = person
    _, other_headers = registered(api)
    foreign = start(api, other_headers)

    for attempt_id in (foreign["id"], str(uuid.uuid4())):
        response = api.post("/api/feedback", headers=headers, json=_body(testAttemptId=attempt_id))
        assert_error(response, 404, "ATTEMPT_NOT_FOUND", "El intento no existe.")
    assert _count(db_session) == 0


def test_a_comment_longer_than_the_maximum_is_rejected(api, person, db_session):
    _, headers = person
    assert api.post("/api/feedback", headers=headers, json=_body(comment="x" * COMMENT_MAX_LENGTH)).status_code == 204
    response = api.post("/api/feedback", headers=headers, json=_body(comment="x" * (COMMENT_MAX_LENGTH + 1)))
    assert_error(response, 400, "VALIDATION_ERROR")
    assert _count(db_session) == 1


@pytest.mark.parametrize(
    "body",
    [
        {"rating": 4, "comment": None},                                    # testAttemptId missing
        {"testAttemptId": None, "comment": None},                          # rating missing
        {"testAttemptId": None, "rating": 4},                              # comment missing
        {**_body(), "userId": str(uuid.uuid4())},                          # identity is the token's
        {**_body(), "testAttemptId": "no-es-un-uuid"},
        [],
    ],
    ids=["no-attempt-key", "no-rating", "no-comment", "user-id", "bad-uuid", "not-an-object"],
)
def test_the_body_is_submit_feedback_input_and_nothing_else(api, person, db_session, body):
    _, headers = person
    assert_error(api.post("/api/feedback", headers=headers, json=body), 400, "VALIDATION_ERROR")
    assert _count(db_session) == 0


def test_feedback_requires_authentication(api, db_session):
    assert_error(api.post("/api/feedback", json=_body()), 401, "UNAUTHORIZED")
    assert _count(db_session) == 0


def test_deleting_the_account_nulls_the_comment_and_keeps_the_rating(api, person, db_session):
    user, headers = person
    attempt = start(api, headers)
    api.post("/api/feedback", headers=headers, json=_body(testAttemptId=attempt["id"], rating=2, comment="Soy yo."))
    api.post("/api/feedback", headers=headers, json=_body(rating=5, comment="General, también mío."))
    other_user, other_headers = registered(api)
    api.post("/api/feedback", headers=other_headers, json=_body(rating=3, comment="De otra persona."))
    before = {(str(row.user_id), row.rating, row.comment) for row in _rows(db_session)}
    print("\nfeedback before:", sorted(before))

    assert api.delete("/api/users/me", headers=headers).status_code == 204

    after = {(str(row.user_id), row.rating, row.comment) for row in _rows(db_session)}
    print("feedback after: ", sorted(after))
    assert after == {
        (user["id"], 2, None),
        (user["id"], 5, None),
        (other_user["id"], 3, "De otra persona."),
    }
