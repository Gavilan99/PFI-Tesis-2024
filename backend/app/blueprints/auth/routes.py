from flask import Blueprint, jsonify, request

from app.blueprints.auth.schemas import AuthOut, LoginIn, RegisterIn
from app.blueprints.schemas import parse_body
from app.blueprints.users.schemas import UserOut
from app.security import identity_provider, public
from app.services import accounts

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _auth_response(result: accounts.AuthenticatedSession, status: int):
    body = AuthOut(
        user=UserOut.model_validate(result.user),
        access_token=result.token.access_token,
        expires_in=result.token.expires_in,
    )
    return jsonify(body.to_json()), status


@bp.post("/register")
@public
def register():
    data = parse_body(RegisterIn, request.get_json(silent=True))
    result = accounts.register(
        identity_provider(),
        username=data.username,
        email=data.email,
        password=data.password.get_secret_value(),
    )
    return _auth_response(result, 201)


@bp.post("/login")
@public
def login():
    data = parse_body(LoginIn, request.get_json(silent=True))
    result = accounts.login(
        identity_provider(), email=data.email, password=data.password.get_secret_value()
    )
    return _auth_response(result, 200)
