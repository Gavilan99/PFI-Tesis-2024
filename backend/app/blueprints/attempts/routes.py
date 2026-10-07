from flask import Blueprint, current_app, jsonify, request

from app.blueprints.attempts.schemas import (
    CreateAttemptIn,
    NewResponseIn,
    QuestionOut,
    TestAttemptOut,
    TestResponseOut,
)
from app.blueprints.schemas import parse_body
from app.db.models.enums import AttemptTier
from app.security import current_user
from app.services import attempts

bp = Blueprint("attempts", __name__, url_prefix="/api/attempts")


def _attempt(attempt):
    return TestAttemptOut.model_validate(attempt).to_json()


@bp.post("")
def create_attempt():
    # No body is the normal case; a body that is there must be valid JSON and pass the schema.
    parse_body(CreateAttemptIn, request.get_json(silent=True) if request.get_data() else {})
    subset_sizes = {
        AttemptTier.FREE_REDUCED: current_app.config["SUBSET_SIZE_FREE_REDUCED"],
        AttemptTier.PAID_FULL: current_app.config["SUBSET_SIZE_PAID_FULL"],
    }
    attempt = attempts.create_attempt(current_user(), subset_sizes)
    return jsonify(_attempt(attempt)), 201


@bp.get("")
def list_attempts():
    return jsonify([_attempt(a) for a in attempts.attempt_history(current_user())])


@bp.get("/latest")
def latest_attempt():
    """No attempt yet is not an error: 200 with a JSON `null`, which is what the contract returns."""
    attempt = attempts.latest_attempt(current_user())
    return jsonify(_attempt(attempt) if attempt is not None else None)


@bp.get("/<uuid:attempt_id>")
def get_attempt(attempt_id):
    return jsonify(_attempt(attempts.get_attempt(current_user(), attempt_id)))


@bp.get("/<uuid:attempt_id>/questions")
def get_questions(attempt_id):
    questions = attempts.served_questions(current_user(), attempt_id)
    return jsonify([QuestionOut.model_validate(q).to_json() for q in questions])


@bp.post("/<uuid:attempt_id>/responses")
def submit_response(attempt_id):
    data = parse_body(NewResponseIn, request.get_json(silent=True))
    response = attempts.submit_response(
        current_user(),
        attempt_id,
        question_id=data.question_id,
        selected_option_id=data.selected_option_id,
    )
    return jsonify(TestResponseOut.model_validate(response).to_json())


@bp.get("/<uuid:attempt_id>/responses")
def get_responses(attempt_id):
    responses = attempts.answered_responses(current_user(), attempt_id)
    return jsonify([TestResponseOut.model_validate(r).to_json() for r in responses])


@bp.post("/<uuid:attempt_id>/complete")
def complete_attempt(attempt_id):
    # Whichever backend CLASSIFIER_BACKEND built at startup; this route never knows which.
    classifier = current_app.extensions["classifier"]
    return jsonify(_attempt(attempts.complete_attempt(current_user(), attempt_id, classifier)))
