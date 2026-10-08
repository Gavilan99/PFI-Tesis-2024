from flask import Blueprint, jsonify

from app.blueprints.results.schemas import ResultOut
from app.security import current_user
from app.services import results

bp = Blueprint("results", __name__, url_prefix="/api/attempts")


@bp.get("/<uuid:attempt_id>/result")
def get_result(attempt_id):
    return jsonify(ResultOut.model_validate(results.get_result(current_user(), attempt_id)).to_json())
