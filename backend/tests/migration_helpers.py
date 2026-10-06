import uuid
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic_config(database_url: str) -> Config:
    """An Alembic config pointed at `database_url`, without reading alembic.ini's logging setup."""
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def rebuild_schema(database_url: str) -> None:
    """Drop everything in the test database and migrate it to head.

    Refuses to touch a database whose name does not end in `_test`.
    """
    url = make_url(database_url)
    if not (url.database or "").endswith("_test"):
        raise RuntimeError(f"Refusing to rebuild a non-test database: {url.database}")

    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    command.upgrade(alembic_config(database_url), "head")


@contextmanager
def scratch_database(base_url: str):
    """Create an empty, uniquely named database on the same server, and drop it afterwards."""
    url = make_url(base_url)
    name = f"nureon_scratch_{uuid.uuid4().hex[:12]}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    try:
        yield url.set(database=name).render_as_string(hide_password=False)
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()
