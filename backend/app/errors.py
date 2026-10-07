import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.exceptions import AppError

logger = logging.getLogger(__name__)

_MESSAGES: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "La solicitud no es válida."),
    401: ("UNAUTHORIZED", "No se pudo autenticar la solicitud."),
    404: ("NOT_FOUND", "El recurso solicitado no existe."),
    405: ("METHOD_NOT_ALLOWED", "El método no está permitido para este recurso."),
    409: ("CONFLICT", "La solicitud entra en conflicto con el estado actual del recurso."),
    422: ("UNPROCESSABLE_ENTITY", "La solicitud no pudo ser procesada."),
    500: ("INTERNAL_SERVER_ERROR", "Ocurrió un error interno."),
}
_DEFAULT = ("HTTP_ERROR", "Ocurrió un error al procesar la solicitud.")


def _error_response(status_code: int, code: str, message: str):
    response = jsonify({"error": {"code": code, "message": message}})
    response.status_code = status_code
    return response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        code, message = _MESSAGES.get(exc.code or 500, _DEFAULT)
        return _error_response(exc.code or 500, code, message)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        logger.exception("Unhandled exception")
        code, message = _MESSAGES[500]
        return _error_response(500, code, message)
