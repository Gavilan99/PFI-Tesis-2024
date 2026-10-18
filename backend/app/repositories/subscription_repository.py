import uuid
from datetime import datetime

from sqlalchemy import exists, or_, select
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
