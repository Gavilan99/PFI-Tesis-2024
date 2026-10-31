from flask import Blueprint, current_app, jsonify

from app.blueprints.results.schemas import PersonalizedDescriptionOut, ResultOut
from app.security import current_user
from app.services import personalized_descriptions, results

bp = Blueprint("results", __name__, url_prefix="/api/attempts")


def _text_generator():
    """`None` with TEXT_GENERATOR=pregenerated (Feature 19): there is no model to call, only the
    pregenerated content `get_personalized_description` reads directly. Any other consumer added
    here must handle that case the same way."""
    return current_app.extensions["text_generator"]


@bp.get("/<uuid:attempt_id>/result")
def get_result(attempt_id):
    return jsonify(ResultOut.model_validate(results.get_result(current_user(), attempt_id)).to_json())


@bp.get("/<uuid:attempt_id>/result/personalized")
def get_personalized_description(attempt_id):
    sections = personalized_descriptions.get_personalized_description(
        _text_generator(), current_user(), attempt_id
    )
    return jsonify(PersonalizedDescriptionOut.model_validate(sections).to_json())
