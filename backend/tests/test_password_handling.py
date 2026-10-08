"""The password passes through this service in transit only: never stored, logged, or echoed.

Logs are captured at DEBUG on every logger that exists, boto's included, so a leak at any level shows.
"""

from sqlalchemy import text

from tests.auth_helpers import register, unique_email
from tests.log_helpers import captured_logs  # noqa: F401  (fixture)

SECRET = "Pw-que-no-debe-aparecer-9f3a1c"


def test_password_never_reaches_the_logs_or_the_responses(api, db_session, captured_logs):
    email = unique_email()
    bodies = []

    bodies.append(register(api, email=email, password=SECRET))                     # success
    bodies.append(register(api, email=email, password=SECRET))                     # duplicate
    bodies.append(register(api, email=unique_email(), password="corta"))          # rejected by validation
    bodies.append(api.post("/api/auth/register", json={"username": "ab", "email": "x", "password": SECRET}))
    bodies.append(api.post("/api/auth/login", json={"email": email, "password": SECRET}))            # success
    bodies.append(api.post("/api/auth/login", json={"email": email, "password": SECRET + "x"}))      # wrong
    bodies.append(api.post("/api/auth/login", json={"email": email, "password": SECRET, "extra": 1}))  # invalid

    assert [r.status_code for r in bodies] == [201, 409, 400, 400, 200, 401, 400]
    assert captured_logs, "nothing was captured: the test would pass vacuously"
    for line in captured_logs:
        assert SECRET not in line
    for response in bodies:
        assert SECRET not in response.get_data(as_text=True)


def test_password_is_not_stored_in_the_database(api, db_session):
    register(api, password=SECRET)
    db_session.commit()
    dump = db_session.execute(text("SELECT row_to_json(u)::text FROM users u")).scalars().all()
    assert dump
    assert not any(SECRET in row for row in dump)


def test_local_double_keeps_only_a_hash(identity):
    identity.create_user("hash@example.test", SECRET, "Hash")
    assert SECRET not in repr(identity._accounts)
    assert all(SECRET.encode() not in account.password_hash for account in identity._accounts.values())
