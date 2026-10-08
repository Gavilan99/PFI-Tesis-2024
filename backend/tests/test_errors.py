def test_404_has_unified_format(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    body = response.get_json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"]


def test_405_has_unified_format(client):
    response = client.post("/api/health")

    assert response.status_code == 405
    body = response.get_json()
    assert body["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert body["error"]["message"]


def test_unhandled_exception_returns_500_without_leaking_the_stack_trace():
    from app import create_app
    from app.security import public

    # A fresh app instance: Flask refuses new routes once an app has handled
    # its first request, so this can't reuse the shared `app`/`client` fixtures.
    boom_app = create_app("test")

    @boom_app.route("/api/_test-only-boom")
    @public
    def _boom():
        raise RuntimeError("kaboom: this must never reach the client")

    response = boom_app.test_client().get("/api/_test-only-boom")

    assert response.status_code == 500
    body = response.get_json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert body["error"]["message"]
    assert "kaboom" not in response.get_data(as_text=True)
    assert "RuntimeError" not in response.get_data(as_text=True)
