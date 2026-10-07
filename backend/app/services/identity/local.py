"""In-memory identity provider, for tests and local development only.

Not a production mode: config refuses `IDENTITY_PROVIDER=local` with `APP_ENV=production`, and
`create_app` checks it again. Accounts live in process memory, so a restart forgets them (the
`users` rows stay; logging in again needs a new registration). Passwords are kept as scrypt
hashes, never in clear, even here.
"""

import hashlib
import hmac
import secrets
import threading
import time
import uuid
from dataclasses import dataclass

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from app.exceptions import EmailAlreadyRegistered, InvalidCredentials, PasswordRejected
from app.services.identity.base import IdentityProvider, IdentityUser, IssuedToken
from app.services.identity.tokens import AccessTokenVerifier

# Same policy the Cognito pool is meant to have: length only, matching the registration form.
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 256


@dataclass
class _Account:
    user: IdentityUser
    salt: bytes
    password_hash: bytes


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


class LocalIdentityProvider(IdentityProvider):
    def __init__(self, pool_id: str = "local-pool", client_id: str = "local-client", token_ttl: int = 3600):
        self.issuer = f"https://local-identity.invalid/{pool_id}"
        self.client_id = client_id
        self.token_ttl = token_ttl
        self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._verifier = AccessTokenVerifier(
            self.issuer, client_id, lambda _token: self._private_key.public_key()
        )
        self._accounts: dict[str, _Account] = {}
        self._sub_by_email: dict[str, str] = {}
        self._lock = threading.Lock()

    def create_user(self, email: str, password: str, display_name: str) -> IdentityUser:
        if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
            raise PasswordRejected()
        salt = secrets.token_bytes(16)
        password_hash = _hash(password, salt)
        with self._lock:
            if email in self._sub_by_email:
                raise EmailAlreadyRegistered()
            user = IdentityUser(sub=str(uuid.uuid4()), email=email, display_name=display_name)
            self._accounts[user.sub] = _Account(user, salt, password_hash)
            self._sub_by_email[email] = user.sub
        return user

    def authenticate(self, email: str, password: str) -> IssuedToken:
        with self._lock:
            sub = self._sub_by_email.get(email)
            account = self._accounts.get(sub) if sub else None
        if account is None or not hmac.compare_digest(account.password_hash, _hash(password, account.salt)):
            raise InvalidCredentials()
        return IssuedToken(self.mint_access_token(account.user.sub), self.token_ttl)

    def verify_access_token(self, token: str) -> str:
        return self._verifier.verify(token)

    def get_user(self, sub: str) -> IdentityUser | None:
        with self._lock:
            account = self._accounts.get(sub)
        return account.user if account else None

    def delete_user(self, sub: str) -> None:
        with self._lock:
            account = self._accounts.pop(sub, None)
            if account:
                self._sub_by_email.pop(account.user.email, None)

    def mint_access_token(
        self,
        sub: str,
        *,
        lifetime: int | None = None,
        issuer: str | None = None,
        client_id: str | None = None,
        token_use: str = "access",
    ) -> str:
        """A token shaped like a Cognito access token. The overrides let tests forge bad ones."""
        now = int(time.time())
        claims = {
            "sub": sub,
            "iss": issuer or self.issuer,
            "client_id": client_id or self.client_id,
            "token_use": token_use,
            "username": sub,
            "iat": now,
            "exp": now + (self.token_ttl if lifetime is None else lifetime),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(claims, self._private_key, algorithm="RS256")
