"""Errors that reach the client. Pure Python: services raise them, `app.errors` renders them.

Each carries its HTTP status, a SNAKE_CASE code and the Spanish message the frontend shows as is.
None of them carries request data: every message is fixed text, never built from input.
"""


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"
    message = "La solicitud no es válida."

    def __init__(self) -> None:
        super().__init__(self.code)


class ValidationFailed(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"
    message = "Los datos enviados no son válidos."


class EmailNotEditable(AppError):
    status_code = 400
    code = "EMAIL_NOT_EDITABLE"
    message = "El email no se puede modificar."


class PasswordRejected(AppError):
    status_code = 400
    code = "PASSWORD_REJECTED"
    message = "La contraseña no cumple los requisitos de seguridad."


class Unauthenticated(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    message = "No se pudo autenticar la solicitud."


class InvalidCredentials(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "Email o contraseña incorrectos."


class EmailAlreadyRegistered(AppError):
    status_code = 409
    code = "EMAIL_ALREADY_REGISTERED"
    message = "Ese email ya está registrado."


class AccountConflict(AppError):
    status_code = 409
    code = "ACCOUNT_CONFLICT"
    message = "La cuenta no se pudo asociar: ya existe otra con ese email."


class IdentityUnavailable(AppError):
    status_code = 503
    code = "IDENTITY_UNAVAILABLE"
    message = "El servicio de cuentas no está disponible. Probá de nuevo en unos minutos."


class TierNotAccepted(AppError):
    status_code = 400
    code = "TIER_NOT_ACCEPTED"
    message = "El tipo de test lo decide el servidor: no se puede elegir al crearlo."


class AttemptNotFound(AppError):
    """Also what someone else's attempt answers: a foreign resource is 404, never 403."""

    status_code = 404
    code = "ATTEMPT_NOT_FOUND"
    message = "El intento no existe."


class AttemptNotInProgress(AppError):
    status_code = 409
    code = "ATTEMPT_NOT_IN_PROGRESS"
    message = "El intento ya no está en curso."


class AttemptIncomplete(AppError):
    status_code = 409
    code = "ATTEMPT_INCOMPLETE"
    message = "Quedan preguntas sin responder: el test no se puede cerrar todavía."


class QuestionNotInAttempt(AppError):
    status_code = 400
    code = "QUESTION_NOT_IN_ATTEMPT"
    message = "La pregunta no forma parte de este intento."


class OptionNotInQuestion(AppError):
    status_code = 400
    code = "OPTION_NOT_IN_QUESTION"
    message = "La opción elegida no corresponde a esa pregunta."


class QuestionnaireUnavailable(AppError):
    """No active version, or one too small to fill a balanced subset. A setup problem, not the user's."""

    status_code = 503
    code = "QUESTIONNAIRE_UNAVAILABLE"
    message = "El cuestionario no está disponible en este momento. Probá de nuevo más tarde."
