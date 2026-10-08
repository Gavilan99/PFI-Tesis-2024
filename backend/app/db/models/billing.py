import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._columns import created_now, fk, uuid_pk
from app.db.models.enums import (
    SubscriptionStatus,
    SubscriptionTier,
    subscription_status_enum,
    subscription_tier_enum,
)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = fk("users.id", nullable=False)
    tier: Mapped[SubscriptionTier] = mapped_column(subscription_tier_enum, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(subscription_status_enum, nullable=False)
    mercadopago_subscription_id: Mapped[str | None] = mapped_column(sa.String(255))
    current_period_start: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = created_now()
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
    )


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        # What makes the Mercado Pago webhook idempotent.
        sa.UniqueConstraint("mercadopago_payment_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    subscription_id: Mapped[uuid.UUID] = fk("subscriptions.id", nullable=False)
    mercadopago_payment_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
