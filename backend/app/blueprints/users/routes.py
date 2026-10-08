from flask import Blueprint, jsonify, request

from app.blueprints.schemas import parse_body
from app.blueprints.users.schemas import UpdateProfileIn, UserOut
from app.security import current_user, identity_provider
from app.services import accounts

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.get("/me")
def get_me():
    return jsonify(UserOut.model_validate(current_user()).to_json())


@bp.patch("/me")
def update_me():
    data = parse_body(UpdateProfileIn, request.get_json(silent=True))
    user = accounts.update_profile(current_user(), data.changes())
    return jsonify(UserOut.model_validate(user).to_json())


@bp.delete("/me")
def delete_me():
    accounts.delete_account(identity_provider(), current_user())
    return "", 204
