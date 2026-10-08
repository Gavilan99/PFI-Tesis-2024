import uuid

PASSWORD = "Contraseña-de-test-1"

USER_FIELDS = {
    "id", "displayName", "email", "accountType", "ageRange", "gender", "country", "professionContext",
}


def unique_email(prefix: str = "persona") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.test"


def register(client, *, email: str | None = None, username: str = "Persona de test", password: str = PASSWORD):
    return client.post(
        "/api/auth/register",
        json={"username": username, "email": email or unique_email(), "password": password},
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def registered(client, **kwargs) -> tuple[dict, dict[str, str]]:
    """Register an account and return (user, auth headers)."""
    response = register(client, **kwargs)
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    return body["user"], bearer(body["accessToken"])


def assert_error(response, status: int, code: str, message: str | None = None) -> None:
    assert response.status_code == status, response.get_json()
    body = response.get_json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code
    if message is not None:
        assert body["error"]["message"] == message
    else:
        assert body["error"]["message"]
