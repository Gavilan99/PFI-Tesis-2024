"""Mercado Pago, reached over HTTPS with the standard library. Two calls, both with the access token:

- `POST /checkout/preferences`: the Checkout Pro preference. Its `init_point` is where the buyer pays.
  https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-pro-preferences/create-preference/post
- `GET /v1/payments/{id}`: the payment as Mercado Pago has it. A notification or a return URL only
  says which payment to look at; this is what is believed.
  https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-pro-preferences/get-payment/get

The preference carries no `notification_url`: notifications come from the URL configured in "Tus
integraciones", which is signed with that configuration's secret and is the only way the documentation
gives to test them. It carries no email or name either: `external_reference` (the users.id) is all
Mercado Pago gets from us.

The token goes in the Authorization header and nowhere else: never in a URL, never in a log line. Logs
name the HTTP status or the exception type, never a response body.
"""

import json
import logging
import socket
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.exceptions import PaymentProviderUnavailable
from app.services.payments.base import CheckoutRequest, PaymentGateway, RemotePayment

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.mercadopago.com"
# Mercado Pago gives a notification 22 seconds for an answer, and the webhook calls this inside it.
TIMEOUT_SECONDS = 10


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


class MercadoPagoGateway(PaymentGateway):
    def __init__(self, access_token: str, *, urlopen: Callable = urllib.request.urlopen):
        if not access_token:
            raise ValueError("Mercado Pago needs an access token.")
        self._token = access_token
        self._urlopen = urlopen

    def _call(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict | None]:
        """(status, JSON body). 4xx are returned for the caller to read; anything else that is not a
        2xx raises PaymentProviderUnavailable."""
        request = urllib.request.Request(
            API_BASE_URL + path,
            method=method,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
        )
        try:
            with self._urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return response.status, json.loads(response.read() or b"null")
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                return exc.code, None
            logger.error("Mercado Pago %s %s answered %s", method, path.split("/")[1], exc.code)
        except (urllib.error.URLError, socket.timeout, TimeoutError, ValueError) as exc:
            logger.error("Mercado Pago %s %s failed: %s", method, path.split("/")[1], type(exc).__name__)
        raise PaymentProviderUnavailable()

    def create_checkout(self, request: CheckoutRequest) -> str:
        status, body = self._call(
            "POST",
            "/checkout/preferences",
            {
                "items": [
                    {
                        "id": request.item_id,
                        "title": request.title,
                        "quantity": 1,
                        "unit_price": float(request.unit_price),
                        "currency_id": request.currency,
                    }
                ],
                "back_urls": {
                    "success": request.return_url,
                    "pending": request.return_url,
                    "failure": request.return_url,
                },
                "auto_return": "approved",
                "external_reference": request.external_reference,
                "expires": True,
                "expiration_date_to": request.expires_at.isoformat(timespec="milliseconds"),
            },
        )
        url = body.get("init_point") if isinstance(body, dict) else None
        if status not in (200, 201) or not url:
            logger.error("Mercado Pago did not create the preference: status %s", status)
            raise PaymentProviderUnavailable()
        return url

    def get_payment(self, payment_id: str) -> RemotePayment | None:
        status, body = self._call("GET", f"/v1/payments/{payment_id}")
        if status in (403, 404):
            # 404: no such payment. 403: not this account's (the token only reads its own payments).
            return None
        if status != 200 or not isinstance(body, dict):
            logger.error("Mercado Pago answered %s for a payment", status)
            raise PaymentProviderUnavailable()
        try:
            return RemotePayment(
                id=str(body["id"]),
                status=str(body["status"]),
                external_reference=body.get("external_reference") or None,
                amount=Decimal(str(body["transaction_amount"])),
                currency=str(body["currency_id"]),
                date_approved=_parse_datetime(body.get("date_approved")),
            )
        except (KeyError, TypeError, InvalidOperation):
            logger.error("Mercado Pago answered a payment without the expected fields")
            raise PaymentProviderUnavailable() from None
