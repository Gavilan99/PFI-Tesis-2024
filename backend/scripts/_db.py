"""Database session for command-line scripts, using the same configuration as the app."""

import os
import sys
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import get_config, load_env_file


def database_url() -> str:
    load_env_file()
    return get_config(os.environ.get("APP_ENV", "development")).SQLALCHEMY_DATABASE_URI


def describe(url: str) -> str:
    parsed = make_url(url)
    return f"{parsed.host}:{parsed.port}/{parsed.database}"


@contextmanager
def open_session(url: str):
    """A session in one transaction. The caller commits; anything not committed is rolled back."""
    engine = create_engine(url)
    try:
        with Session(engine) as session:
            try:
                yield session
            finally:
                session.rollback()
    finally:
        engine.dispose()


def utf8_output() -> None:
    """Spanish output stays readable when piped on Windows, where the default is cp1252."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
