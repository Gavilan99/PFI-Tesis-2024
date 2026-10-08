"""The history chain, end to end: what the profile reads (Feature 3 and 4.1), checked together.

Two closed attempts and one in progress: the history lists the three newest first, and each closed one
has its result while the one in progress has none.
"""

from tests.attempt_helpers import answer_all, questions, start
from tests.auth_helpers import assert_error, registered


def _close(api, headers) -> dict:
    attempt = start(api, headers)
    answer_all(api, headers, attempt["id"], questions(api, headers, attempt["id"]))
    response = api.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def test_history_lists_newest_first_and_only_closed_attempts_have_a_result(api, question_bank):
    _, headers = registered(api)
    oldest = _close(api, headers)
    middle = _close(api, headers)
    newest = start(api, headers)

    history = api.get("/api/attempts", headers=headers).get_json()

    assert [(a["id"], a["status"]) for a in history] == [
        (newest["id"], "in_progress"),
        (middle["id"], "completed"),
        (oldest["id"], "completed"),
    ]
    for closed in (middle, oldest):
        response = api.get(f"/api/attempts/{closed['id']}/result", headers=headers)
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["testAttemptId"] == closed["id"]
    assert_error(api.get(f"/api/attempts/{newest['id']}/result", headers=headers), 404, "RESULT_NOT_FOUND")
