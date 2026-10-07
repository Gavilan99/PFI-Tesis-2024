QUESTION_FIELDS = {"id", "questionType", "promptText", "displayOrder", "answerOptions"}
OPTION_FIELDS = {"id", "questionId", "optionText", "displayOrder"}
ATTEMPT_FIELDS = {
    "id", "userId", "subjectId", "tier", "questionnaireVersion", "status", "startedAt", "completedAt",
}
RESPONSE_FIELDS = {
    "id", "testAttemptId", "questionId", "selectedOptionId", "freeTextResponse", "orderingResponse",
    "answeredAt",
}


def answer_body(question_id: str, option_id: str | None, **overrides) -> dict:
    return {
        "questionId": question_id,
        "selectedOptionId": option_id,
        "freeTextResponse": None,
        "orderingResponse": None,
        **overrides,
    }


def start(client, headers) -> dict:
    response = client.post("/api/attempts", headers=headers)
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def questions(client, headers, attempt_id: str) -> list[dict]:
    response = client.get(f"/api/attempts/{attempt_id}/questions", headers=headers)
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def answer(client, headers, attempt_id: str, question: dict, position: int = 0):
    option_id = question["answerOptions"][position]["id"]
    return client.post(
        f"/api/attempts/{attempt_id}/responses", headers=headers, json=answer_body(question["id"], option_id)
    )


def answer_all(client, headers, attempt_id: str, items: list[dict]) -> None:
    for item in items:
        response = answer(client, headers, attempt_id, item)
        assert response.status_code == 200, response.get_json()
