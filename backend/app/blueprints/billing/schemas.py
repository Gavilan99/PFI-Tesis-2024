from datetime import datetime
from typing import Annotated

from pydantic import StringConstraints

from app.blueprints.schemas import ApiModel, ApiOutput
from app.services.billing import PaymentOutcome

# Mercado Pago payment ids are numbers. Only digits reach a URL or a query towards Mercado Pago.
PAYMENT_ID_PATTERN = r"^\d{1,20}$"
PaymentId = Annotated[str, StringConstraints(strip_whitespace=True, pattern=PAYMENT_ID_PATTERN)]


class ConfirmPaymentIn(ApiModel):
    """The body of `confirmPayment(paymentId)`: which payment to look at, nothing about its outcome."""

    payment_id: PaymentId


class SubscriptionOut(ApiOutput):
    """`Subscription` (subscription.model.ts). The plan's price is shown, never sent back."""

    active: bool
    current_period_end: datetime | None
    plan_price: float
    plan_currency: str
    plan_days: int


class CheckoutSessionOut(ApiOutput):
    """`CheckoutSession` (subscription.model.ts)."""

    checkout_url: str


class PaymentConfirmationOut(ApiOutput):
    """`PaymentConfirmation` (subscription.model.ts)."""

    payment_status: PaymentOutcome  # approved | pending | rejected
    current_period_end: datetime | None
