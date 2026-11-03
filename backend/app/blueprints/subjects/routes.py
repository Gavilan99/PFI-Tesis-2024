from flask import Blueprint, jsonify

from app.blueprints.subjects.schemas import SubjectOut
from app.security import current_user
from app.services import subjects

bp = Blueprint("subjects", __name__, url_prefix="/api/subjects")


@bp.get("")
def list_subjects():
    return jsonify([SubjectOut.model_validate(s).to_json() for s in subjects.list_subjects(current_user())])


@bp.delete("/<uuid:subject_id>")
def delete_subject(subject_id):
    subjects.delete_subject(current_user(), subject_id)
    return "", 204
