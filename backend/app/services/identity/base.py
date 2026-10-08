"""The identity seam: what the backend needs from an identity provider, and nothing else.

Two implementations: `CognitoIdentityProvider` (the real one) and `LocalIdentityProvider` (a double
for tests and local development, refused in production). Passwords go through these methods in
transit only: no implementation stores them in clear, logs them, or puts them in an exception.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class IdentityUser:
    sub: str
    email: str
    display_name: str | None


@dataclass(frozen=True)
class IssuedToken:
    access_token: str
    expires_in: int


class IdentityProvider(ABC):
    @abstractmethod
    def create_user(self, email: str, password: str, display_name: str) -> IdentityUser:
        """Create a confirmed account. Raises EmailAlreadyRegistered or PasswordRejected."""

    @abstractmethod
    def authenticate(self, email: str, password: str) -> IssuedToken:
        """Raises InvalidCredentials whatever the reason: unknown email and wrong password look alike."""

    @abstractmethod
    def verify_access_token(self, token: str) -> str:
        """Return the token's `sub`. Raises Unauthenticated on any failure."""

    @abstractmethod
    def get_user(self, sub: str) -> IdentityUser | None:
        """The account behind `sub`, or None if it does not exist (or no longer does)."""

    @abstractmethod
    def delete_user(self, sub: str) -> None:
        """Delete the account. Deleting one that does not exist is not an error."""
