"""Someone else's attempt is a 404 on every endpoint, exactly like one that does not exist, and
nothing about it changes."""

import pytest

from tests.attempt_helpers import answer_all, answer_body, questions, start
from tests.auth_helpers import assert_error, registered


@pytest.fixture()
def two_people(api, question_bank):
    return registered(api), registered(api)


def test_another_user_cannot_read_or_answer_my_attempt(api, two_people):
    (_, mine), (_, theirs) = two_people
    attempt = start(api, mine)
    items = questions(api, mine, attempt["id"])
    answer_all(api, mine, attempt["id"], items[:2])
    path = f"/api/attempts/{attempt['id']}"
    snapshot = (
        api.get(path, headers=mine).get_json(),
        api.get(f"{path}/responses", headers=mine).get_json(),
    )

    body = answer_body(items[3]["id"], items[3]["answerOptions"][0]["id"])
    for response in (
        api.get(path, headers=theirs),
        api.get(f"{path}/questions", headers=theirs),
        api.get(f"{path}/responses", headers=theirs),
        api.post(f"{path}/responses", headers=theirs, json=body),
        api.post(f"{path}/complete", headers=theirs),
    ):
        assert_error(response, 404, "ATTEMPT_NOT_FOUND", "El intento no existe.")

    assert (
        api.get(path, headers=mine).get_json(),
        api.get(f"{path}/responses", headers=mine).get_json(),
    ) == snapshot


def test_another_user_cannot_overwrite_my_answer(api, two_people):
    (_, mine), (_, theirs) = two_people
    attempt = start(api, mine)
    item = questions(api, mine, attempt["id"])[0]
    answer_all(api, mine, attempt["id"], [item])
    other_option = item["answerOptions"][1]["id"]
    response = api.post(
        f"/api/attempts/{attempt['id']}/responses", headers=theirs, json=answer_body(item["id"], other_option)
    )
    assert_error(response, 404, "ATTEMPT_NOT_FOUND")
    stored = api.get(f"/api/attempts/{attempt['id']}/responses", headers=mine).get_json()
    assert stored[0]["selectedOptionId"] == item["answerOptions"][0]["id"]


def test_another_user_cannot_complete_my_attempt(api, two_people):
    (_, mine), (_, theirs) = two_people
    attempt = start(api, mine)
    answer_all(api, mine, attempt["id"], questions(api, mine, attempt["id"]))
    response = api.post(f"/api/attempts/{attempt['id']}/complete", headers=theirs)
    assert_error(response, 404, "ATTEMPT_NOT_FOUND")
    assert api.get(f"/api/attempts/{attempt['id']}", headers=mine).get_json()["status"] == "in_progress"


def test_my_attempts_are_not_in_their_lists(api, two_people):
    (_, mine), (_, theirs) = two_people
    start(api, mine)
    assert api.get("/api/attempts", headers=theirs).get_json() == []
    assert api.get("/api/attempts/latest", headers=theirs).get_json() is None


def test_starting_an_attempt_does_not_abandon_someone_elses(api, two_people):
    (_, mine), (_, theirs) = two_people
    attempt = start(api, mine)
    start(api, theirs)
    assert api.get(f"/api/attempts/{attempt['id']}", headers=mine).get_json()["status"] == "in_progress"
