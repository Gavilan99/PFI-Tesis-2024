import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Payment, Subscription


def recorded_period_end(session: Session, mercadopago_payment_id: str) -> tuple[bool, datetime | None]:
    """(whether the payment is already recorded, the end of the period it bought)."""
    row = session.execute(
        select(Subscription.current_period_end)
        .join(Payment, Payment.subscription_id == Subscription.id)
        .where(Payment.mercadopago_payment_id == mercadopago_payment_id)
    ).first()
    return (row is not None, row[0] if row is not None else None)


def insert(
    session: Session,
    *,
    subscription_id: uuid.UUID,
    mercadopago_payment_id: str,
    amount: Decimal,
    currency: str,
    status: str,
    paid_at: datetime | None,
) -> Payment:
    payment = Payment(
        subscription_id=subscription_id,
        mercadopago_payment_id=mercadopago_payment_id,
        amount=amount,
        currency=currency,
        status=status,
        paid_at=paid_at,
    )
    session.add(payment)
    session.flush()
    return payment
