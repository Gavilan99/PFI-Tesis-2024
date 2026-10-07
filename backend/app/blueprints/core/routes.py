from flask import Blueprint, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.security import public

bp = Blueprint("core", __name__)


@bp.get("/api/health")
@public
def health():
    return jsonify({"status": "ok"})


@bp.get("/api/health/ready")
@public
def health_ready():
    engine = current_app.extensions["sqlalchemy_engine"]
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        current_app.logger.exception("Readiness check failed")
        response = jsonify(
            {
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "El servicio no está listo: no se pudo conectar con la base de datos.",
                }
            }
        )
        response.status_code = 503
        return response
    return jsonify({"status": "ok"})
