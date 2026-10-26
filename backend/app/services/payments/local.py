"""In-memory payment gateway, for tests and local development only. Nothing leaves the process.

Not a production mode: config refuses `PAYMENT_PROVIDER=local` with `APP_ENV=production`, and the app
factory checks the object it built again. A restart forgets every payment.

A checkout is approved on the spot: `create_checkout` records an approved payment for the exact price
asked and answers the backend's own return URL with its id, so the whole flow (button, return screen,
the same attempt going on) can be walked locally without Mercado Pago. Tests add payments in any state
with `add_payment`.
"""

import itertools
import threading
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode

from app.services.payments.base import CheckoutRequest, PaymentGateway, RemotePayment


class LocalPaymentGateway(PaymentGateway):
    def __init__(self):
        self._payments: dict[str, RemotePayment] = {}
        self._checkouts: list[CheckoutRequest] = []
        # Mercado Pago payment ids are numbers; these never collide with a test's own.
        self._ids = itertools.count(900_000_001)
        self._lock = threading.Lock()

    def create_checkout(self, request: CheckoutRequest) -> str:
        payment = self.add_payment(
            external_reference=request.external_reference,
            amount=request.unit_price,
            currency=request.currency,
            status="approved",
        )
        with self._lock:
            self._checkouts.append(request)
        return f"{request.return_url}?{urlencode({'payment_id': payment.id})}"

    def get_payment(self, payment_id: str) -> RemotePayment | None:
        with self._lock:
            return self._payments.get(payment_id)

    def add_payment(
        self,
        *,
        external_reference: str | None,
        amount: Decimal,
        currency: str = "ARS",
        status: str = "approved",
        payment_id: str | None = None,
    ) -> RemotePayment:
        with self._lock:
            payment_id = payment_id or str(next(self._ids))
            payment = RemotePayment(
                id=payment_id,
                status=status,
                external_reference=external_reference,
                amount=Decimal(amount),
                currency=currency,
                date_approved=datetime.now(timezone.utc) if status == "approved" else None,
            )
            self._payments[payment_id] = payment
            return payment

    @property
    def checkouts(self) -> list[CheckoutRequest]:
        with self._lock:
            return list(self._checkouts)
