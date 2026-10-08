"""Accounts: registration, login, the authenticated user, profile edits and deletion (RF01, RF02, RF07).

The `users` row is tied to the identity provider's `sub`. It is created on registration and, as a
fallback, on the first authenticated request of an account that exists in the provider but not here.
Emails are normalized (trimmed, lowercased) before they reach the provider or the database.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import User
from app.db.session import Session
from app.exceptions import AccountConflict, EmailAlreadyRegistered, Unauthenticated
from app.repositories import user_repository
from app.services.identity import IdentityProvider, IssuedToken


@dataclass(frozen=True)
class AuthenticatedSession:
    user: User
    token: IssuedToken


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register(identity: IdentityProvider, *, username: str, email: str, password: str) -> AuthenticatedSession:
    session = Session()
    email = normalize_email(email)
    if user_repository.live_email_exists(session, email):
        raise EmailAlreadyRegistered()

    created = identity.create_user(email, password, username)
    try:
        user = _provision(session, sub=created.sub, email=email, display_name=username)
        session.commit()
    except Exception:
        # Without its row the new account would hold the email in the provider and nowhere else.
        session.rollback()
        identity.delete_user(created.sub)
        raise
    return AuthenticatedSession(user, identity.authenticate(email, password))


def login(identity: IdentityProvider, *, email: str, password: str) -> AuthenticatedSession:
    token = identity.authenticate(normalize_email(email), password)
    user = authenticated_user(identity, identity.verify_access_token(token.access_token))
    return AuthenticatedSession(user, token)


def authenticated_user(identity: IdentityProvider, sub: str) -> User:
    """The live user behind a verified token's `sub`, provisioning the row if it is missing.

    A deleted account has no row with its `sub` any more, and no account in the provider either,
    so its old tokens end here as Unauthenticated.
    """
    session = Session()
    user = user_repository.get_live_by_sub(session, sub)
    if user is not None:
        return user

    account = identity.get_user(sub)
    if account is None:
        raise Unauthenticated()
    email = normalize_email(account.email)
    user = _provision(session, sub=sub, email=email, display_name=account.display_name or email.split("@")[0])
    session.commit()
    return user


def update_profile(user: User, changes: dict) -> User:
    session = Session()
    user_repository.update_profile(session, user, changes)
    session.commit()
    return user


def delete_account(identity: IdentityProvider, user: User) -> None:
    """Soft delete with anonymization (Ley 25.326), then delete the account in the provider.

    The row is anonymized first, inside the transaction; the provider account is deleted before
    committing. If the provider fails, nothing is committed and the account stays as it was.
    """
    session = Session()
    locked = user_repository.get_live_by_sub(session, user.cognito_sub, for_update=True)
    if locked is None:
        raise Unauthenticated()
    sub = locked.cognito_sub
    user_repository.anonymize(session, locked, datetime.now(timezone.utc))
    try:
        identity.delete_user(sub)
    except Exception:
        session.rollback()
        raise
    session.commit()


def _provision(session, *, sub: str, email: str, display_name: str | None) -> User:
    user = user_repository.insert_if_absent(session, sub=sub, email=email, display_name=display_name)
    if user is None:
        session.rollback()
        raise AccountConflict()
    return user
