"""The payments seam: the two things the backend asks Mercado Pago, and nothing else.

Two implementations: `MercadoPagoGateway` (the real one, Checkout Pro) and `LocalPaymentGateway` (a
double for tests and local development, refused in production). Same pattern and same reason as the
identity and mail seams: the suite never depends on Mercado Pago.

A gateway never decides anything: it creates the checkout the backend describes and reports a payment
as Mercado Pago has it. Whether that payment buys the plan is `app.services.billing`'s call.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CheckoutRequest:
    """One Checkout Pro preference: a single item, at the price of the backend's configuration."""

    external_reference: str  # the buyer's users.id: how a payment is traced back to the account
    item_id: str
    title: str
    unit_price: Decimal
    currency: str
    return_url: str  # success, pending and failure all come back here
    expires_at: datetime


@dataclass(frozen=True)
class RemotePayment:
    """A payment as `GET /v1/payments/{id}` reports it: only the fields the backend uses."""

    id: str
    status: str
    external_reference: str | None
    amount: Decimal
    currency: str
    date_approved: datetime | None


class PaymentGateway(ABC):
    @abstractmethod
    def create_checkout(self, request: CheckoutRequest) -> str:
        """The URL the buyer is sent to. Raises PaymentProviderUnavailable on any failure."""

    @abstractmethod
    def get_payment(self, payment_id: str) -> RemotePayment | None:
        """None when Mercado Pago has no such payment for this account (404, or 403 for someone else's).
        Raises PaymentProviderUnavailable on any other failure."""
