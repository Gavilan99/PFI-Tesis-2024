"""Accounts: registration, login, the authenticated user, profile edits and deletion (RF01, RF02, RF07).

The `users` row is tied to the identity provider's `sub`. It is created on registration and, outside
production, as a fallback, on the first authenticated request of an account that exists in the provider
but not here. In production that account is refused instead (`AccountNotEnabled`, Feature 11).
Emails are normalized (trimmed, lowercased) before they reach the provider or the database.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import User
from app.db.session import Session
from app.exceptions import (
    AccountConflict,
    AccountNotEnabled,
    ConsentRequired,
    EmailAlreadyRegistered,
    Unauthenticated,
)
from app.repositories import user_repository
from app.services.identity import IdentityProvider, IssuedToken


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthenticatedSession:
    user: User
    token: IssuedToken


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register(
    identity: IdentityProvider,
    *,
    username: str,
    email: str,
    password: str,
    consent_accepted: bool,
    consent_version: str,
) -> AuthenticatedSession:
    """`consent_version` is the version in force, from configuration: the client never chooses it."""
    if consent_accepted is not True:
        raise ConsentRequired()
    session = Session()
    email = normalize_email(email)
    if user_repository.live_email_exists(session, email):
        raise EmailAlreadyRegistered()

    created = identity.create_user(email, password, username)
    try:
        user = _provision(
            session,
            sub=created.sub,
            email=email,
            display_name=username,
            consent_accepted_at=datetime.now(timezone.utc),
            consent_version=consent_version,
        )
        session.commit()
    except Exception:
        # Without its row the new account would hold the email in the provider and nowhere else.
        session.rollback()
        identity.delete_user(created.sub)
        raise
    return AuthenticatedSession(user, identity.authenticate(email, password))


def login(identity: IdentityProvider, *, email: str, password: str, provision_missing: bool) -> AuthenticatedSession:
    token = identity.authenticate(normalize_email(email), password)
    user = authenticated_user(
        identity, identity.verify_access_token(token.access_token), provision_missing=provision_missing
    )
    return AuthenticatedSession(user, token)


def authenticated_user(identity: IdentityProvider, sub: str, *, provision_missing: bool) -> User:
    """The live user behind a verified token's `sub`, provisioning the row if it is missing.

    A deleted account has no row with its `sub` any more, and no account in the provider either,
    so its old tokens end here as Unauthenticated.

    `provision_missing` is False in production: an account that exists in the provider but never went
    through the registration has no consent recorded, so it gets no row and is refused.
    """
    session = Session()
    user = user_repository.get_live_by_sub(session, sub)
    if user is not None:
        return user

    account = identity.get_user(sub)
    if account is None:
        raise Unauthenticated()
    if not provision_missing:
        logger.warning("Refused an account that exists in the identity provider but has no users row")
        raise AccountNotEnabled()
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


def _provision(session, *, sub: str, email: str, display_name: str | None, **consent) -> User:
    user = user_repository.insert_if_absent(session, sub=sub, email=email, display_name=display_name, **consent)
    if user is None:
        session.rollback()
        raise AccountConflict()
    return user
