from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

session_factory = sessionmaker(autoflush=False, autocommit=False, future=True)
Session = scoped_session(session_factory)

cors = CORS()


def init_db(app: Flask) -> None:
    engine = create_engine(
        app.config["SQLALCHEMY_DATABASE_URI"], future=True, pool_pre_ping=True
    )
    session_factory.configure(bind=engine)
    app.extensions["sqlalchemy_engine"] = engine

    @app.teardown_appcontext
    def remove_session(exception: BaseException | None = None) -> None:
        Session.remove()
