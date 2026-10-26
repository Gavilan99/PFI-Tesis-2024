"""Feature 6: the plan's state, starting a checkout, confirming a payment on the way back, and the two
routes Mercado Pago calls (the notification and the return), which carry no session.
"""

import re
from urllib.parse import urlencode

from flask import Blueprint, current_app, redirect, request

from app.blueprints.billing.schemas import (
    PAYMENT_ID_PATTERN,
    CheckoutSessionOut,
    ConfirmPaymentIn,
    PaymentConfirmationOut,
    SubscriptionOut,
)
from app.blueprints.schemas import parse_body
from app.config import FRONTEND_RETURN_PATH
from app.exceptions import InvalidWebhookSignature
from app.security import current_user, public
from app.services import billing
from app.services.payments import signature

bp = Blueprint("billing", __name__, url_prefix="/api")

_PAYMENT_ID = re.compile(PAYMENT_ID_PATTERN)


def _gateway():
    return current_app.extensions["payment_gateway"]


def _plan() -> billing.Plan:
    return billing.Plan.from_config(current_app.config)


@bp.get("/subscription")
def get_subscription():
    return SubscriptionOut.model_validate(billing.subscription_state(current_user(), _plan())).to_json()


@bp.post("/checkout")
def start_checkout():
    url = billing.start_checkout(
        current_user(), _gateway(), _plan(), return_url=current_app.config["PAYMENT_RETURN_URL"]
    )
    return CheckoutSessionOut(checkout_url=url).to_json()


@bp.post("/checkout/confirm")
def confirm_payment():
    data = parse_body(ConfirmPaymentIn, request.get_json(silent=True))
    confirmation = billing.confirm_payment(current_user(), _gateway(), _plan(), data.payment_id)
    return PaymentConfirmationOut.model_validate(confirmation).to_json()


@bp.post("/payments/webhook")
@public
def payment_notification():
    """Mercado Pago's notification. 401 unless signed with the application's secret; 200 for anything
    signed that is not a payment, or a payment that does not exist; 502 when Mercado Pago cannot be
    read, so it retries. Answers within its 22 seconds: one call, with a 10-second timeout."""
    data_id = request.args.get("data.id")
    if not signature.is_valid(
        current_app.config["MERCADOPAGO_WEBHOOK_SECRET"],
        x_signature=request.headers.get("x-signature"),
        request_id=request.headers.get("x-request-id"),
        data_id=data_id,
    ):
        raise InvalidWebhookSignature()
    body = request.get_json(silent=True)
    kind = request.args.get("type") or (body.get("type") if isinstance(body, dict) else None)
    if kind == "payment" and data_id and _PAYMENT_ID.match(data_id):
        billing.handle_notification(_gateway(), _plan(), data_id)
    return "", 200


@bp.get("/payments/return")
@public
def payment_return():
    """Where Mercado Pago sends the buyer back when the frontend is on localhost, which it refuses
    (PUBLIC_API_BASE_URL, a tunnel: config.PAYMENT_RETURN_URL). Forwards only the payment id, and only when it looks like one; the status Mercado Pago appends is
    dropped on purpose: the frontend asks the backend, which asks Mercado Pago."""
    target = current_app.config["FRONTEND_BASE_URL"] + FRONTEND_RETURN_PATH
    payment_id = (request.args.get("payment_id") or "").strip()
    if _PAYMENT_ID.match(payment_id):
        target += "?" + urlencode({"payment_id": payment_id})
    return redirect(target, code=302)
