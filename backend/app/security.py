"""Authentication, in one place: every route requires a verified access token unless marked `@public`.

Deny by default, so a new route cannot forget it. The identity comes from the token and from
nowhere else: no header, parameter or body field the client sends can claim to be someone (the old
code trusted a `userType` header; anyone could declare themselves a professional).
"""

from collections.abc import Callable

from flask import Flask, current_app, g, request

from app.db.models import User
from app.exceptions import Unauthenticated
from app.services import accounts
from app.services.identity import IdentityProvider

_PUBLIC_ATTR = "_public_endpoint"


def public(view: Callable) -> Callable:
    setattr(view, _PUBLIC_ATTR, True)
    return view


def identity_provider() -> IdentityProvider:
    return current_app.extensions["identity_provider"]


def current_user() -> User:
    return g.current_user


def _bearer_token() -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise Unauthenticated()
    return token.strip()


def init_auth(app: Flask) -> None:
    @app.before_request
    def authenticate_request():
        # No endpoint means routing failed: let the 404/405 handlers answer.
        if request.endpoint is None or request.method == "OPTIONS":
            return None
        view = app.view_functions.get(request.endpoint)
        if view is None or getattr(view, _PUBLIC_ATTR, False):
            return None
        provider = identity_provider()
        g.current_user = accounts.authenticated_user(provider, provider.verify_access_token(_bearer_token()))
        return None
