from sqlalchemy.exc import SQLAlchemyError


def test_health_does_not_touch_database(client, app, monkeypatch):
    engine = app.extensions["sqlalchemy_engine"]

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("GET /api/health must not touch the database")

    monkeypatch.setattr(engine, "connect", _fail_if_called)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_ready_ok(client, db_session):
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_ready_returns_503_when_db_unreachable(client, app, monkeypatch):
    class _BrokenEngine:
        def connect(self):
            raise SQLAlchemyError("could not connect")

    monkeypatch.setitem(app.extensions, "sqlalchemy_engine", _BrokenEngine())

    response = client.get("/api/health/ready")

    assert response.status_code == 503
    body = response.get_json()
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert body["error"]["message"]
