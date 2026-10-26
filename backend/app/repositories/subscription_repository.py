import uuid
from datetime import datetime

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Subscription
from app.db.models.enums import SubscriptionStatus, SubscriptionTier


def has_active(session: Session, user_id: uuid.UUID, now: datetime) -> bool:
    """An `active` subscription whose period has no end or ends after `now`."""
    return bool(
        session.scalar(
            select(
                exists().where(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    or_(Subscription.current_period_end.is_(None), Subscription.current_period_end > now),
                )
            )
        )
    )


def insert_manual(
    session: Session, user_id: uuid.UUID, *, tier: SubscriptionTier, start: datetime, end: datetime
) -> Subscription:
    """A subscription with no payment behind it: `mercadopago_subscription_id` stays NULL."""
    subscription = Subscription(
        user_id=user_id,
        tier=tier,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=start,
        current_period_end=end,
    )
    session.add(subscription)
    session.flush()
    return subscription


def active_period_end(session: Session, user_id: uuid.UUID, now: datetime) -> datetime | None:
    """The latest end among the account's active, unexpired periods. None when there is none, or when
    the only active ones have no end."""
    return session.scalar(
        select(func.max(Subscription.current_period_end)).where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.current_period_end > now,
        )
    )


def insert_paid(
    session: Session,
    user_id: uuid.UUID,
    *,
    tier: SubscriptionTier,
    start: datetime,
    end: datetime,
    mercadopago_reference: str,
) -> Subscription:
    """A period bought through Mercado Pago. With Checkout Pro there is no Mercado Pago subscription:
    `mercadopago_subscription_id` holds the id of the payment that bought it, so it is never NULL on a
    paid row (NULL is a manual grant, `insert_manual`)."""
    subscription = Subscription(
        user_id=user_id,
        tier=tier,
        status=SubscriptionStatus.ACTIVE,
        mercadopago_subscription_id=mercadopago_reference,
        current_period_start=start,
        current_period_end=end,
    )
    session.add(subscription)
    session.flush()
    return subscription
