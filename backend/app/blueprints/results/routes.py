from flask import Blueprint, current_app, jsonify

from app.blueprints.results.schemas import PersonalizedDescriptionOut, ResultOut
from app.security import current_user
from app.services import personalized_descriptions, results

bp = Blueprint("results", __name__, url_prefix="/api/attempts")


@bp.get("/<uuid:attempt_id>/result")
def get_result(attempt_id):
    return jsonify(ResultOut.model_validate(results.get_result(current_user(), attempt_id)).to_json())


@bp.get("/<uuid:attempt_id>/result/personalized")
def get_personalized_description(attempt_id):
    generator = current_app.extensions["text_generator"]
    sections = personalized_descriptions.get_personalized_description(generator, current_user(), attempt_id)
    return jsonify(PersonalizedDescriptionOut.model_validate(sections).to_json())
