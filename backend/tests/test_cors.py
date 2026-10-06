def test_disallowed_origin_gets_no_cors_header(client):
    response = client.get("/api/health", headers={"Origin": "https://not-allowed.example"})

    assert "Access-Control-Allow-Origin" not in response.headers


def test_allowed_origin_gets_cors_header(client, app):
    allowed_origin = app.config["CORS_ALLOWED_ORIGINS"][0]

    response = client.get("/api/health", headers={"Origin": allowed_origin})

    assert response.headers.get("Access-Control-Allow-Origin") == allowed_origin
