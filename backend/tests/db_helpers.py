from contextlib import contextmanager

from sqlalchemy import event

from app.extensions import Session, session_factory


@contextmanager
def bound_session(app):
    """Yield a session whose writes are rolled back, and restore the global session factory afterwards.

    The shared factory is pointed at a connection for the duration of the block only. Its original
    bind is restored in `finally`, so later tests (and the app) see the engine again.
    """
    engine = app.extensions["sqlalchemy_engine"]
    original_bind = session_factory.kw.get("bind")

    connection = engine.connect()
    transaction = connection.begin()
    session_factory.configure(bind=connection)
    session = Session()
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", _restart_savepoint)
        session.close()
        Session.remove()
        session_factory.configure(bind=original_bind)
        transaction.rollback()
        connection.close()


def option_ids(question) -> list:
    """Bank order: what a response row stores as `option_order` when nothing shuffled it."""
    return [option.id for option in question.answer_options]
