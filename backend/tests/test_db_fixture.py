import pytest
from sqlalchemy import text

from app.extensions import session_factory
from tests.db_helpers import bound_session


def test_bound_session_restores_original_bind(app):
    original_bind = session_factory.kw.get("bind")

    with bound_session(app) as session:
        assert session_factory.kw.get("bind") is not original_bind
        assert session.execute(text("SELECT 1")).scalar() == 1

    assert session_factory.kw.get("bind") is original_bind


def test_bound_session_restores_bind_when_the_test_fails(app):
    original_bind = session_factory.kw.get("bind")

    with pytest.raises(RuntimeError):
        with bound_session(app):
            raise RuntimeError("test body failed")

    assert session_factory.kw.get("bind") is original_bind


def test_bound_session_rolls_back_ddl_and_writes(app):
    with bound_session(app) as session:
        session.execute(text("CREATE TABLE _fixture_probe (id integer)"))
        session.execute(text("INSERT INTO _fixture_probe VALUES (1)"))

    engine = app.extensions["sqlalchemy_engine"]
    with engine.connect() as connection:
        exists = connection.execute(text("SELECT to_regclass('_fixture_probe')")).scalar()
    assert exists is None
