"""Paying for the full plan (Feature 6): Mercado Pago Checkout Pro, one payment per period.

One payment buys the individual plan for `PLAN_INDIVIDUAL_DAYS`; there is no automatic renewal (a
recurring subscription is post-MVP: a scope limitation of the thesis). Price, currency and period are
configuration, never code and never the client's.

The server is the only source of the tier. The browser starts a checkout and, coming back, says which
payment to look at; whether it bought anything is read from Mercado Pago (`GET /v1/payments/{id}`) and
decided here. A notification (the webhook) and the buyer coming back (`confirm`) run the same
idempotent `_record`, so it does not matter which arrives first: the first records the payment, the
second finds it recorded. The UNIQUE on `payments.mercadopago_payment_id` makes that hold even when
both arrive at once.

An approved payment writes one `subscriptions` row (tier `individual`, `active`, the period) and one
`payments` row, together. Pending and rejected payments write nothing: there is nothing to undo when
a pending one is approved later, which arrives as another notification. Refunds and chargebacks are
out of scope: they are logged and change nothing.

Payment states, as Mercado Pago documents them:
https://www.mercadopago.com.ar/developers/es/docs/checkout-api-payments/response-handling/query-results
"""

import enum
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.db.models import User
from app.db.models.enums import SubscriptionTier
from app.db.session import Session
from app.exceptions import AlreadySubscribed, PaymentNotFound
from app.repositories import payment_repository, subscription_repository, user_repository
from app.services import tiers
from app.services.payments import CheckoutRequest, PaymentGateway, RemotePayment

logger = logging.getLogger(__name__)

PLAN_ITEM_ID = "individual"
# A preference is only payable for a while, so a price change leaves few checkouts open at the old one.
CHECKOUT_TTL = timedelta(minutes=30)


class PaymentOutcome(enum.StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


_OUTCOMES = {
    "approved": PaymentOutcome.APPROVED,
    "pending": PaymentOutcome.PENDING,
    "authorized": PaymentOutcome.PENDING,
    "in_process": PaymentOutcome.PENDING,
    "in_mediation": PaymentOutcome.PENDING,
    "rejected": PaymentOutcome.REJECTED,
    "cancelled": PaymentOutcome.REJECTED,
}


@dataclass(frozen=True)
class Plan:
    price: Decimal
    currency: str
    days: int

    @classmethod
    def from_config(cls, config) -> "Plan":
        return cls(
            price=config["PLAN_INDIVIDUAL_PRICE"],
            currency=config["PLAN_INDIVIDUAL_CURRENCY"],
            days=config["PLAN_INDIVIDUAL_DAYS"],
        )

    @property
    def title(self) -> str:
        return f"NureonAI · plan completo por {self.days} días"


@dataclass(frozen=True)
class SubscriptionState:
    active: bool
    current_period_end: datetime | None
    plan_price: Decimal
    plan_currency: str
    plan_days: int


@dataclass(frozen=True)
class PaymentConfirmation:
    payment_status: PaymentOutcome
    current_period_end: datetime | None


def subscription_state(user: User, plan: Plan) -> SubscriptionState:
    session = Session()
    now = datetime.now(timezone.utc)
    return SubscriptionState(
        active=tiers.has_paid_tier(session, user.id, now),
        current_period_end=subscription_repository.active_period_end(session, user.id, now),
        plan_price=plan.price,
        plan_currency=plan.currency,
        plan_days=plan.days,
    )


def start_checkout(user: User, gateway: PaymentGateway, plan: Plan, *, return_url: str) -> str:
    """The Checkout Pro URL for this account, at the configured price. 409 with the paid tier."""
    if tiers.has_paid_tier(Session(), user.id):
        raise AlreadySubscribed()
    return gateway.create_checkout(
        CheckoutRequest(
            external_reference=str(user.id),
            item_id=PLAN_ITEM_ID,
            title=plan.title,
            unit_price=plan.price,
            currency=plan.currency,
            return_url=return_url,
            expires_at=datetime.now(timezone.utc) + CHECKOUT_TTL,
        )
    )


def confirm_payment(user: User, gateway: PaymentGateway, plan: Plan, payment_id: str) -> PaymentConfirmation:
    """The buyer, back from Mercado Pago, asks about the payment the return URL named. Someone else's
    payment answers like one that does not exist."""
    payment = gateway.get_payment(payment_id)
    if payment is None or payment.external_reference != str(user.id):
        raise PaymentNotFound()
    return _record(payment, plan)


def handle_notification(gateway: PaymentGateway, plan: Plan, payment_id: str) -> None:
    """A signed `payment` notification. Never trusts its body: only which payment to read."""
    payment = gateway.get_payment(payment_id)
    if payment is None:
        logger.warning("Payment notification for a payment Mercado Pago does not have: %s", payment_id)
        return
    _record(payment, plan)


def _record(payment: RemotePayment, plan: Plan) -> PaymentConfirmation:
    session = Session()
    outcome = _OUTCOMES.get(payment.status)
    if outcome is None:
        # refunded, charged_back or anything new: out of scope, nothing changes.
        logger.warning("Payment %s is %s: nothing recorded", payment.id, payment.status)
        return PaymentConfirmation(PaymentOutcome.REJECTED, None)
    if outcome is not PaymentOutcome.APPROVED:
        logger.info("Payment %s is %s: nothing recorded yet", payment.id, payment.status)
        return PaymentConfirmation(outcome, None)

    recorded, end = payment_repository.recorded_period_end(session, payment.id)
    if recorded:
        return PaymentConfirmation(PaymentOutcome.APPROVED, end)

    user = _payer(session, payment.external_reference)
    if user is None:
        logger.error("Approved payment %s does not name a live account: nothing recorded", payment.id)
        return PaymentConfirmation(PaymentOutcome.REJECTED, None)
    if payment.currency != plan.currency or payment.amount != plan.price:
        # Only this backend creates preferences with this token, so this means the price changed while a
        # checkout was open. Money was taken: the team grants the period by hand (grant_subscription.py).
        logger.error(
            "Approved payment %s does not match the plan (%s %s): nothing recorded, review by hand",
            payment.id, plan.currency, plan.price,
        )
        return PaymentConfirmation(PaymentOutcome.PENDING, None)

    now = datetime.now(timezone.utc)
    # Paying while a period is still running (two tabs, two payments) adds to it instead of overlapping.
    start = max(now, subscription_repository.active_period_end(session, user.id, now) or now)
    end = start + timedelta(days=plan.days)
    try:
        with session.begin_nested():
            subscription = subscription_repository.insert_paid(
                session, user.id, tier=SubscriptionTier.INDIVIDUAL, start=start, end=end,
                mercadopago_reference=payment.id,
            )
            payment_repository.insert(
                session,
                subscription_id=subscription.id,
                mercadopago_payment_id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status,
                paid_at=payment.date_approved or now,
            )
    except IntegrityError:
        # The other path (webhook or confirm) recorded it in between: one row, theirs. Leaving the
        # savepoint already rolled back only this attempt.
        _, end = payment_repository.recorded_period_end(session, payment.id)
        return PaymentConfirmation(PaymentOutcome.APPROVED, end)
    session.commit()
    logger.info("Payment %s recorded: subscription %s until %s", payment.id, subscription.id, end.date())
    return PaymentConfirmation(PaymentOutcome.APPROVED, end)


def _payer(session, external_reference: str | None) -> User | None:
    try:
        user_id = uuid.UUID(str(external_reference))
    except ValueError:
        return None
    return user_repository.get_live(session, user_id)
