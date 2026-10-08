from flask import Blueprint, current_app, request

from app.blueprints.feedback.schemas import SubmitContactMessageIn, SubmitFeedbackIn
from app.blueprints.schemas import parse_body
from app.security import current_user, public
from app.services import contact, feedback

bp = Blueprint("feedback", __name__, url_prefix="/api")


@bp.post("/feedback")
def submit_feedback():
    data = parse_body(SubmitFeedbackIn, request.get_json(silent=True))
    feedback.submit_feedback(
        current_user(), test_attempt_id=data.test_attempt_id, rating=data.rating, comment=data.comment
    )
    return "", 204


@bp.post("/contact-messages")
@public
def submit_contact_message():
    data = parse_body(SubmitContactMessageIn, request.get_json(silent=True))
    contact.send_contact_message(
        current_app.extensions["mail_sender"],
        current_app.extensions["contact_rate_limiter"],
        # The connecting address. Behind the ALB (Feature 8) this needs ProxyFix, or every request
        # shares the balancer's address and the limit becomes global.
        origin=request.remote_addr or "unknown",
        name=data.name,
        email=data.email,
        message=data.message,
        mail_to=current_app.config["CONTACT_MAIL_TO"],
        mail_from=current_app.config["CONTACT_MAIL_FROM"],
    )
    return "", 204
