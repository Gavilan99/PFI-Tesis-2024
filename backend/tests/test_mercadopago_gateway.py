"""The real gateway, without the network: what it sends to Mercado Pago and how it reads the answers.

`urlopen` is replaced by a fake that records the request and answers what each test says. Nothing here
reaches api.mercadopago.com.
"""

import io
import json
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.exceptions import PaymentProviderUnavailable
from app.services.payments import CheckoutRequest, MercadoPagoGateway
from tests.log_helpers import captured_logs  # noqa: F401  (fixture)

TOKEN = "APP_USR-0000000000000000-000000-test-token-not-real"


class _Response(io.BytesIO):
    def __init__(self, status: int, body):
        super().__init__(json.dumps(body).encode())
        self.status = status


class FakeUrlopen:
    def __init__(self, status: int = 200, body=None, error: Exception | None = None):
        self.status, self.body, self.error = status, body, error
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        if self.error is not None:
            raise self.error
        if self.status >= 400:
            raise urllib.error.HTTPError(request.full_url, self.status, "error", {}, io.BytesIO(b"{}"))
        return _Response(self.status, self.body)


def _checkout() -> CheckoutRequest:
    return CheckoutRequest(
        external_reference="5d0f6c3e-0000-4000-8000-000000000001",
        item_id="individual",
        title="NureonAI · plan completo por 30 días",
        unit_price=Decimal("4999.00"),
        currency="ARS",
        return_url="https://api.example.test/api/payments/return",
        expires_at=datetime(2026, 10, 25, 12, 30, tzinfo=timezone.utc),
    )


def test_the_preference_is_the_documented_body_with_the_token_in_the_header_only():
    fake = FakeUrlopen(201, {"id": "pref-1", "init_point": "https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=1"})
    url = MercadoPagoGateway(TOKEN, urlopen=fake).create_checkout(_checkout())

    assert url == "https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=1"
    [(request, timeout)] = fake.requests
    assert (request.get_method(), request.full_url) == ("POST", "https://api.mercadopago.com/checkout/preferences")
    assert request.get_header("Authorization") == f"Bearer {TOKEN}"
    assert TOKEN not in request.full_url and timeout <= 10
    body = json.loads(request.data)
    assert body["items"] == [{
        "id": "individual", "title": "NureonAI · plan completo por 30 días", "quantity": 1,
        "unit_price": 4999.0, "currency_id": "ARS",
    }]
    assert body["back_urls"] == {key: "https://api.example.test/api/payments/return"
                                 for key in ("success", "pending", "failure")}
    assert body["auto_return"] == "approved"
    assert body["external_reference"] == "5d0f6c3e-0000-4000-8000-000000000001"
    assert body["expires"] is True and body["expiration_date_to"].startswith("2026-10-25T12:30:00.000")
    # Nothing that identifies the person beyond the account id, and no notification_url (the panel's).
    assert "payer" not in body and "notification_url" not in body


def test_a_payment_is_read_with_the_fields_the_backend_uses():
    fake = FakeUrlopen(200, {
        "id": 123456789, "status": "approved", "status_detail": "accredited", "external_reference": "abc",
        "transaction_amount": 4999, "currency_id": "ARS", "date_approved": "2026-10-25T10:00:00.000-03:00",
    })
    payment = MercadoPagoGateway(TOKEN, urlopen=fake).get_payment("123456789")
    assert (payment.id, payment.status, payment.external_reference) == ("123456789", "approved", "abc")
    assert (payment.amount, payment.currency) == (Decimal("4999"), "ARS")
    assert payment.date_approved == datetime.fromisoformat("2026-10-25T10:00:00.000-03:00")
    [(request, _)] = fake.requests
    assert request.full_url == "https://api.mercadopago.com/v1/payments/123456789"


@pytest.mark.parametrize("status", [403, 404])
def test_a_payment_that_is_not_there_or_not_ours_is_none(status):
    assert MercadoPagoGateway(TOKEN, urlopen=FakeUrlopen(status)).get_payment("1") is None


@pytest.mark.parametrize("fake", [
    FakeUrlopen(500),
    FakeUrlopen(503),
    FakeUrlopen(error=urllib.error.URLError("unreachable")),
    FakeUrlopen(error=TimeoutError()),
    FakeUrlopen(200, {"id": 1}),  # without the fields
])
def test_any_other_failure_is_unavailable(fake):
    with pytest.raises(PaymentProviderUnavailable):
        MercadoPagoGateway(TOKEN, urlopen=fake).get_payment("1")


def test_a_preference_without_init_point_is_unavailable():
    with pytest.raises(PaymentProviderUnavailable):
        MercadoPagoGateway(TOKEN, urlopen=FakeUrlopen(201, {"id": "pref"})).create_checkout(_checkout())
    with pytest.raises(PaymentProviderUnavailable):
        MercadoPagoGateway(TOKEN, urlopen=FakeUrlopen(400)).create_checkout(_checkout())


def test_the_access_token_never_reaches_a_log_line(captured_logs):
    for fake in (FakeUrlopen(500), FakeUrlopen(error=urllib.error.URLError(TOKEN)), FakeUrlopen(200, {})):
        with pytest.raises(PaymentProviderUnavailable):
            MercadoPagoGateway(TOKEN, urlopen=fake).get_payment("1")
    assert captured_logs, "the failures were expected to be logged"
    assert not any(TOKEN in line for line in captured_logs)


def test_the_gateway_needs_a_token():
    with pytest.raises(ValueError):
        MercadoPagoGateway("")
