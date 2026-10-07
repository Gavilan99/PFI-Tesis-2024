"""The scoped session shared by services and repositories. Knows nothing about Flask."""

from sqlalchemy.orm import scoped_session, sessionmaker

session_factory = sessionmaker(autoflush=False, autocommit=False, future=True)
Session = scoped_session(session_factory)
