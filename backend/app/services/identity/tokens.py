"""Access-token verification, shared by both identity providers.

Checks the signature against the provider's keys, the issuer, the expiration, `token_use` (access
tokens only: an ID token is rejected) and `client_id` (Cognito access tokens carry no `aud`).
"""

import logging
from collections.abc import Callable
from typing import Any

import jwt

from app.exceptions import IdentityUnavailable, Unauthenticated

logger = logging.getLogger(__name__)

ALGORITHMS = ["RS256"]
REQUIRED_CLAIMS = ["exp", "iss", "sub", "token_use", "client_id"]


class AccessTokenVerifier:
    def __init__(self, issuer: str, client_id: str, key_for_token: Callable[[str], Any]):
        self.issuer = issuer
        self.client_id = client_id
        self._key_for_token = key_for_token

    def verify(self, token: str) -> str:
        try:
            key = self._key_for_token(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=ALGORITHMS,
                issuer=self.issuer,
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.PyJWKClientConnectionError:
            logger.warning("Could not fetch the identity provider's signing keys")
            raise IdentityUnavailable() from None
        except jwt.PyJWTError as exc:
            logger.info("Rejected access token: %s", type(exc).__name__)
            raise Unauthenticated() from None

        if claims.get("token_use") != "access" or claims.get("client_id") != self.client_id:
            logger.info("Rejected access token: wrong token_use or client_id")
            raise Unauthenticated()
        return claims["sub"]
