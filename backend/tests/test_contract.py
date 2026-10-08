"""The contract, route by route: the exact key set of every response equals the TypeScript interface it
is read as.

The expected keys are not written here. They are parsed from the frontend's own source
(`frontend/nureon/src/app/core/models/` and the `AuthResponse` envelope in `http-api.service.ts`), so a
field added or removed on either side fails this test. Equality, not containment: a key too many is as
much a defect as a key too few.

One request per `ApiService` method, fourteen in all, with the local identity and the filler bank. A
test also checks that the fourteen here are exactly the methods `ApiService` declares.
"""

import re
from pathlib import Path

import pytest

from tests.attempt_helpers import answer_body
from tests.auth_helpers import PASSWORD, bearer, unique_email

FRONTEND_CORE = Path(__file__).resolve().parents[2] / "frontend" / "nureon" / "src" / "app" / "core"
MODELS = FRONTEND_CORE / "models"
SERVICES = FRONTEND_CORE / "services"

# `//` not preceded by a colon or a quote, so "http://..." inside a string is not taken for a comment.
_LINE_COMMENT = re.compile(r"(^|[^:'\"`])//[^\n]*", re.MULTILINE)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_PROPERTY = re.compile(r"^\s*(?:readonly\s+)?([A-Za-z_]\w*)\??\s*:")
_METHOD = re.compile(r"^\s*([A-Za-z_]\w*)\s*\(")


def _strip_comments(source: str) -> str:
    return _LINE_COMMENT.sub(r"\1", _BLOCK_COMMENT.sub("", source))


def _interface_body(path: Path, name: str) -> list[str]:
    source = _strip_comments(path.read_text(encoding="utf-8"))
    match = re.search(rf"\binterface\s+{name}\b[^{{]*\{{", source)
    assert match, f"interface {name} not found in {path}"
    depth, start = 1, match.end()
    for index in range(start, len(source)):
        depth += {"{": 1, "}": -1}.get(source[index], 0)
        if depth == 0:
            break
    body = source[start:index]
    # Only top-level members: a nested object type's members are not the interface's.
    lines, depth = [], 0
    for line in body.splitlines():
        if depth == 0:
            lines.append(line)
        depth += line.count("{") + line.count("(") - line.count("}") - line.count(")")
    return lines


def ts_keys(file: str, name: str, folder: Path = MODELS) -> set[str]:
    """The property names of a TypeScript interface, read from the frontend source."""
    keys = {m.group(1) for line in _interface_body(folder / file, name) if (m := _PROPERTY.match(line))}
    assert keys, f"interface {name} has no properties"
    return keys


def ts_methods(file: str, name: str, folder: Path = SERVICES) -> set[str]:
    return {m.group(1) for line in _interface_body(folder / file, name) if (m := _METHOD.match(line))}


@pytest.fixture(scope="module")
def shapes() -> dict[str, set[str]]:
    if not FRONTEND_CORE.is_dir():
        pytest.fail(f"The frontend contract is not in the working tree: {FRONTEND_CORE}")
    return {
        "AuthResponse": ts_keys("http-api.service.ts", "AuthResponse", SERVICES),
        "User": ts_keys("user.model.ts", "User"),
        "TestAttempt": ts_keys("test-attempt.model.ts", "TestAttempt"),
        "Question": ts_keys("question.model.ts", "Question"),
        "AnswerOption": ts_keys("answer-option.model.ts", "AnswerOption"),
        "TestResponse": ts_keys("response.model.ts", "TestResponse"),
        "Result": ts_keys("result.model.ts", "Result"),
    }


def test_the_parser_reads_the_interfaces_it_is_trusted_with(shapes):
    # A guard on the guard: if the parser silently dropped keys, every equality below could pass on
    # two equally wrong sets. These are the shapes as of Feature 7, written once, by hand.
    assert shapes["User"] == {
        "id", "displayName", "email", "accountType", "ageRange", "gender", "country", "professionContext",
    }
    assert shapes["Question"] == {"id", "questionType", "promptText", "displayOrder", "answerOptions"}
    assert shapes["Result"] == {"id", "testAttemptId", "eneatype", "descriptionText", "generatedAt"}
    assert shapes["AuthResponse"] == {"user", "accessToken", "expiresIn"}


def _keys(body) -> set[str]:
    assert isinstance(body, dict), body
    return set(body)


def _empty(response) -> bool:
    return response.status_code == 204 and response.get_data() == b""


def test_every_route_answers_exactly_the_shape_of_its_interface(api, question_bank, shapes):
    checked: dict[str, bool] = {}
    email = unique_email("contrato")

    # register(input) -> POST /api/auth/register
    response = api.post(
        "/api/auth/register", json={"username": "Persona contrato", "email": email, "password": PASSWORD}
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    checked["register"] = _keys(body) == shapes["AuthResponse"] and _keys(body["user"]) == shapes["User"]

    # login(input) -> POST /api/auth/login
    response = api.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    checked["login"] = _keys(body) == shapes["AuthResponse"] and _keys(body["user"]) == shapes["User"]
    headers = bearer(body["accessToken"])

    # getLatestAttempt(userId) -> GET /api/attempts/latest, before any attempt: the contract's null.
    response = api.get("/api/attempts/latest", headers=headers)
    assert response.status_code == 200, response.get_json()
    latest_when_none = response.get_json() is None

    # updateProfile(userId, input) -> PATCH /api/users/me
    response = api.patch("/api/users/me", headers=headers, json={"country": "Argentina"})
    assert response.status_code == 200, response.get_json()
    checked["updateProfile"] = _keys(response.get_json()) == shapes["User"]

    # createTestAttempt(userId) -> POST /api/attempts
    response = api.post("/api/attempts", headers=headers)
    assert response.status_code == 201, response.get_json()
    attempt = response.get_json()
    checked["createTestAttempt"] = _keys(attempt) == shapes["TestAttempt"]
    attempt_url = f"/api/attempts/{attempt['id']}"

    # getQuestions(attemptId) -> GET /api/attempts/{id}/questions
    response = api.get(f"{attempt_url}/questions", headers=headers)
    assert response.status_code == 200, response.get_json()
    items = response.get_json()
    assert items
    checked["getQuestions"] = all(
        _keys(q) == shapes["Question"] and q["answerOptions"]
        and all(_keys(o) == shapes["AnswerOption"] for o in q["answerOptions"])
        for q in items
    )

    # submitResponse(attemptId, response) -> POST /api/attempts/{id}/responses
    submitted = []
    for item in items:
        response = api.post(
            f"{attempt_url}/responses",
            headers=headers,
            json=answer_body(item["id"], item["answerOptions"][0]["id"]),
        )
        assert response.status_code == 200, response.get_json()
        submitted.append(response.get_json())
    checked["submitResponse"] = all(_keys(r) == shapes["TestResponse"] for r in submitted)

    # getResponses(attemptId) -> GET /api/attempts/{id}/responses
    response = api.get(f"{attempt_url}/responses", headers=headers)
    assert response.status_code == 200, response.get_json()
    responses = response.get_json()
    checked["getResponses"] = len(responses) == len(items) and all(
        _keys(r) == shapes["TestResponse"] for r in responses
    )

    # completeTestAttempt(attemptId) -> POST /api/attempts/{id}/complete
    response = api.post(f"{attempt_url}/complete", headers=headers)
    assert response.status_code == 200, response.get_json()
    checked["completeTestAttempt"] = _keys(response.get_json()) == shapes["TestAttempt"]

    # getLatestAttempt(userId) -> GET /api/attempts/latest, with an attempt.
    response = api.get("/api/attempts/latest", headers=headers)
    assert response.status_code == 200, response.get_json()
    checked["getLatestAttempt"] = latest_when_none and _keys(response.get_json()) == shapes["TestAttempt"]

    # getAttempt(attemptId) -> GET /api/attempts/{id}
    response = api.get(attempt_url, headers=headers)
    assert response.status_code == 200, response.get_json()
    checked["getAttempt"] = _keys(response.get_json()) == shapes["TestAttempt"]

    # getAttemptHistory(userId) -> GET /api/attempts
    response = api.get("/api/attempts", headers=headers)
    assert response.status_code == 200, response.get_json()
    history = response.get_json()
    checked["getAttemptHistory"] = len(history) == 1 and all(_keys(a) == shapes["TestAttempt"] for a in history)

    # getResult(attemptId) -> GET /api/attempts/{id}/result
    response = api.get(f"{attempt_url}/result", headers=headers)
    assert response.status_code == 200, response.get_json()
    checked["getResult"] = _keys(response.get_json()) == shapes["Result"]

    # submitFeedback(input) -> POST /api/feedback: Observable<void>, so no body at all.
    response = api.post(
        "/api/feedback", headers=headers, json={"testAttemptId": attempt["id"], "rating": 5, "comment": None}
    )
    checked["submitFeedback"] = _empty(response)

    # submitContactMessage(input) -> POST /api/contact-messages: public, and no body either.
    response = api.post(
        "/api/contact-messages",
        json={"name": "Persona contrato", "email": email, "message": "Un mensaje de contrato."},
    )
    checked["submitContactMessage"] = _empty(response)

    assert set(checked) == ts_methods("api.service.ts", "ApiService"), "a method of ApiService is not covered"
    assert [name for name, ok in checked.items() if not ok] == []
