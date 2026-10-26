"""Feature 6: paying for the full plan with Mercado Pago Checkout Pro, through the local gateway.

The server is the only source of the tier: the browser starts a checkout and, coming back, names a
payment; whether it bought the plan is what the gateway (Mercado Pago, in production) reports. The
webhook and the return run the same idempotent recording: one `payments` row per Mercado Pago payment,
whatever arrives first and however often.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.models import Payment, Subscription, TestAttempt
from app.services.payments import signature
from tests.attempt_helpers import start
from tests.auth_helpers import assert_error, registered
from tests.cut_helpers import answer_everything, continue_, cut, give_paid_tier
from tests.log_helpers import captured_logs  # noqa: F401  (fixture)

SECRET = "test-webhook-secret"
PRICE = Decimal("4999.00")  # the example plan TestConfig fixes


@pytest.fixture()
def webhook_secret(app, monkeypatch):
    monkeypatch.setitem(app.config, "MERCADOPAGO_WEBHOOK_SECRET", SECRET)
    return SECRET


@pytest.fixture()
def person(api, question_bank):
    return registered(api)


def _payments(db_session, payment_id: str) -> list[Payment]:
    db_session.expire_all()
    return db_session.scalars(select(Payment).where(Payment.mercadopago_payment_id == payment_id)).all()


def _subscriptions(db_session, user_id) -> list[Subscription]:
    db_session.expire_all()
    return db_session.scalars(select(Subscription).where(Subscription.user_id == uuid.UUID(user_id))).all()


def _notify(api, payment_id: str, *, secret: str = SECRET, request_id: str = "req-1", ts: str = "1742505638683",
            kind: str = "payment", signature_header: str | None = None):
    header = signature_header
    if header is None:
        header = f"ts={ts},v1={signature.sign(secret, data_id=payment_id, request_id=request_id, ts=ts)}"
    return api.post(
        f"/api/payments/webhook?data.id={payment_id}&type={kind}",
        headers={"x-signature": header, "x-request-id": request_id},
        json={"action": "payment.updated", "type": kind, "data": {"id": payment_id}},
    )


def _confirm(api, headers, payment_id: str):
    return api.post("/api/checkout/confirm", headers=headers, json={"paymentId": payment_id})


# --- the signature -------------------------------------------------------------------------------


def test_the_manifest_is_the_documented_template():
    # The documentation's own example values, with data.id lowercased as it asks.
    assert signature.manifest(
        data_id="ORD01JQ4S4KY8HWQ6NA5PXB65B3D3", request_id="2066ca19-c6f1-498a-be75-1923005edd06",
        ts="1742505638683",
    ) == "id:ord01jq4s4ky8hwq6na5pxb65b3d3;request-id:2066ca19-c6f1-498a-be75-1923005edd06;ts:1742505638683;"


def test_a_part_that_did_not_arrive_is_left_out_of_the_manifest():
    assert signature.manifest(data_id=None, request_id="r", ts="1") == "request-id:r;ts:1;"
    assert signature.manifest(data_id="5", request_id=None, ts="1") == "id:5;ts:1;"


def test_a_signature_is_valid_only_with_the_same_secret_and_values():
    v1 = signature.sign(SECRET, data_id="123", request_id="r", ts="1")
    assert signature.is_valid(SECRET, x_signature=f"ts=1,v1={v1}", request_id="r", data_id="123")
    assert not signature.is_valid("other", x_signature=f"ts=1,v1={v1}", request_id="r", data_id="123")
    assert not signature.is_valid(SECRET, x_signature=f"ts=2,v1={v1}", request_id="r", data_id="123")
    assert not signature.is_valid(SECRET, x_signature=f"ts=1,v1={v1}", request_id="r", data_id="124")
    assert not signature.is_valid(SECRET, x_signature=f"ts=1,v1={v1}", request_id="x", data_id="123")
    assert not signature.is_valid(SECRET, x_signature="garbage", request_id="r", data_id="123")
    assert not signature.is_valid(SECRET, x_signature=None, request_id="r", data_id="123")
    # Without a configured secret nothing is ever valid.
    assert not signature.is_valid("", x_signature=f"ts=1,v1={v1}", request_id="r", data_id="123")


# --- the webhook ---------------------------------------------------------------------------------


def test_a_validly_signed_approved_payment_buys_the_plan(api, person, payments, webhook_secret, db_session):
    user, headers = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE)

    assert _notify(api, payment.id).status_code == 200

    rows = _payments(db_session, payment.id)
    assert len(rows) == 1
    assert (rows[0].amount, rows[0].currency, rows[0].status) == (PRICE, "ARS", "approved")
    [subscription] = _subscriptions(db_session, user["id"])
    assert rows[0].subscription_id == subscription.id
    assert (subscription.tier.value, subscription.status.value) == ("individual", "active")
    # Never NULL on a paid row: NULL is what tells a manual grant apart.
    assert subscription.mercadopago_subscription_id == payment.id
    assert subscription.current_period_end - subscription.current_period_start == timedelta(days=30)
    assert api.get("/api/subscription", headers=headers).get_json()["active"] is True


def test_an_invalid_signature_is_401_and_records_nothing(api, person, payments, webhook_secret, db_session):
    user, _ = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE)

    assert_error(_notify(api, payment.id, secret="not-the-secret"), 401, "INVALID_SIGNATURE")
    assert_error(_notify(api, payment.id, signature_header="ts=1,v1=00"), 401, "INVALID_SIGNATURE")
    response = api.post(f"/api/payments/webhook?data.id={payment.id}&type=payment", json={})
    assert_error(response, 401, "INVALID_SIGNATURE")

    assert _payments(db_session, payment.id) == []
    assert _subscriptions(db_session, user["id"]) == []


@pytest.mark.parametrize("status", ["pending", "in_process", "authorized"])
def test_a_pending_payment_records_nothing_yet(api, person, payments, webhook_secret, db_session, status):
    user, _ = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE, status=status)
    assert _notify(api, payment.id).status_code == 200
    assert _payments(db_session, payment.id) == []
    assert _subscriptions(db_session, user["id"]) == []


@pytest.mark.parametrize("status", ["rejected", "cancelled", "refunded", "charged_back"])
def test_a_rejected_payment_records_nothing(api, person, payments, webhook_secret, db_session, status):
    user, _ = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE, status=status)
    assert _notify(api, payment.id).status_code == 200
    assert _payments(db_session, payment.id) == []
    assert _subscriptions(db_session, user["id"]) == []


def test_a_pending_payment_approved_later_is_recorded_then(api, person, payments, webhook_secret, db_session):
    user, _ = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE, status="pending")
    assert _notify(api, payment.id).status_code == 200
    payments.add_payment(external_reference=user["id"], amount=PRICE, status="approved", payment_id=payment.id)
    assert _notify(api, payment.id, request_id="req-2").status_code == 200
    assert len(_payments(db_session, payment.id)) == 1


def test_a_repeated_notification_records_one_payment(api, person, payments, webhook_secret, db_session):
    user, _ = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE)
    for request_id in ("req-1", "req-1", "req-2"):
        assert _notify(api, payment.id, request_id=request_id).status_code == 200
    assert len(_payments(db_session, payment.id)) == 1
    assert len(_subscriptions(db_session, user["id"])) == 1


def test_a_notification_for_a_payment_that_does_not_exist_is_200_and_records_nothing(
    api, payments, webhook_secret, db_session
):
    assert _notify(api, "123456789").status_code == 200
    assert _payments(db_session, "123456789") == []


def test_a_signed_notification_that_is_not_a_payment_is_ignored(api, person, payments, webhook_secret, db_session):
    user, _ = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE)
    assert _notify(api, payment.id, kind="merchant_order").status_code == 200
    assert _payments(db_session, payment.id) == []


def test_an_approved_payment_that_names_no_live_account_records_nothing(api, payments, webhook_secret, db_session):
    payment = payments.add_payment(external_reference=str(uuid.uuid4()), amount=PRICE)
    assert _notify(api, payment.id).status_code == 200
    assert _payments(db_session, payment.id) == []


def test_an_approved_payment_for_another_amount_records_nothing(
    api, person, payments, webhook_secret, db_session, captured_logs
):
    user, _ = person
    payment = payments.add_payment(external_reference=user["id"], amount=Decimal("1.00"))
    assert _notify(api, payment.id).status_code == 200
    assert _payments(db_session, payment.id) == []
    assert any("does not match the plan" in line for line in captured_logs)


def test_mercado_pago_unavailable_is_502_so_it_retries(api, payments, webhook_secret, monkeypatch):
    from app.exceptions import PaymentProviderUnavailable

    def unavailable(payment_id):
        raise PaymentProviderUnavailable()

    monkeypatch.setattr(payments, "get_payment", unavailable)
    assert_error(_notify(api, "123"), 502, "PAYMENT_PROVIDER_UNAVAILABLE")


# --- the buyer: checkout, return, confirm ----------------------------------------------------------


def test_the_subscription_shows_the_configured_plan_without_one(api, person):
    _, headers = person
    response = api.get("/api/subscription", headers=headers)
    assert response.status_code == 200
    assert response.get_json() == {
        "active": False, "currentPeriodEnd": None, "planPrice": 4999.0, "planCurrency": "ARS", "planDays": 30,
    }


def test_checkout_asks_for_the_configured_price_and_names_the_account(api, person, payments, app):
    user, headers = person
    response = api.post("/api/checkout", headers=headers)
    assert response.status_code == 200, response.get_json()
    assert set(response.get_json()) == {"checkoutUrl"}
    [request] = payments.checkouts
    assert (request.unit_price, request.currency, request.external_reference) == (PRICE, "ARS", user["id"])
    assert request.return_url == app.config["PAYMENT_RETURN_URL"] == "http://localhost:4200/pago"
    assert request.expires_at > datetime.now(timezone.utc)


def test_the_client_cannot_set_the_price(api, person, payments):
    _, headers = person
    response = api.post("/api/checkout", headers=headers, json={"price": 1, "tier": "paid_full"})
    assert response.status_code == 200
    assert payments.checkouts[0].unit_price == PRICE


def test_checkout_with_the_plan_active_is_409(api, person, db_session):
    user, headers = person
    give_paid_tier(db_session, user["id"])
    assert_error(api.post("/api/checkout", headers=headers), 409, "ALREADY_SUBSCRIBED")


def test_confirm_records_an_approved_payment_once_whoever_comes_first(
    api, person, payments, webhook_secret, db_session
):
    user, headers = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE)

    first = _confirm(api, headers, payment.id)
    assert first.status_code == 200, first.get_json()
    assert first.get_json()["paymentStatus"] == "approved"
    assert first.get_json()["currentPeriodEnd"] is not None
    # The notification arriving after the buyer: nothing new.
    assert _notify(api, payment.id).status_code == 200
    again = _confirm(api, headers, payment.id)
    assert again.get_json() == first.get_json()
    assert len(_payments(db_session, payment.id)) == 1


def test_the_notification_before_the_buyer_comes_back(api, person, payments, webhook_secret, db_session):
    user, headers = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE)
    assert _notify(api, payment.id).status_code == 200
    response = _confirm(api, headers, payment.id)
    assert response.get_json()["paymentStatus"] == "approved"
    assert len(_payments(db_session, payment.id)) == 1


@pytest.mark.parametrize(("status", "expected"), [("pending", "pending"), ("rejected", "rejected")])
def test_confirm_reports_pending_and_rejected_without_the_plan(api, person, payments, db_session, status, expected):
    user, headers = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE, status=status)
    response = _confirm(api, headers, payment.id)
    assert response.get_json() == {"paymentStatus": expected, "currentPeriodEnd": None}
    assert _subscriptions(db_session, user["id"]) == []


def test_another_accounts_payment_answers_like_one_that_does_not_exist(api, person, payments, db_session):
    _, headers = person
    other, _ = registered(api)
    payment = payments.add_payment(external_reference=other["id"], amount=PRICE)
    assert_error(_confirm(api, headers, payment.id), 404, "PAYMENT_NOT_FOUND", "No encontramos ese pago.")
    assert_error(_confirm(api, headers, "987654321"), 404, "PAYMENT_NOT_FOUND", "No encontramos ese pago.")
    assert _payments(db_session, payment.id) == []


def test_without_a_session_every_buyer_route_is_401(api, payments):
    for method, url in (("get", "/api/subscription"), ("post", "/api/checkout"), ("post", "/api/checkout/confirm")):
        assert_error(getattr(api, method)(url, json={"paymentId": "1"}), 401, "UNAUTHORIZED")


@pytest.mark.parametrize("payment_id", ["", "abc", "1; drop", "1" * 21, 123])
def test_confirm_only_accepts_a_numeric_payment_id(api, person, payment_id):
    _, headers = person
    assert_error(api.post("/api/checkout/confirm", headers=headers, json={"paymentId": payment_id}), 400,
                 "VALIDATION_ERROR")


def test_the_return_forwards_only_the_payment_id(api, app):
    response = api.get("/api/payments/return?payment_id=123&status=approved&external_reference=x")
    assert response.status_code == 302
    assert response.headers["Location"] == app.config["FRONTEND_BASE_URL"] + "/pago?payment_id=123"
    response = api.get("/api/payments/return?payment_id=evil.example&status=approved")
    assert response.headers["Location"] == app.config["FRONTEND_BASE_URL"] + "/pago"


# --- RF17: whoever pays after the free cut goes on in the same attempt -----------------------------


def test_paying_at_the_free_cut_continues_the_same_attempt(api, person, payments, db_session):
    user, headers = person
    attempt = start(api, headers)
    answer_everything(api, headers, attempt["id"])
    assert_error(continue_(api, headers, attempt["id"]), 402, "PAID_TIER_REQUIRED")

    # The local gateway approves on the spot and answers the return URL with the payment id.
    checkout_url = api.post("/api/checkout", headers=headers).get_json()["checkoutUrl"]
    payment_id = checkout_url.split("payment_id=")[1]
    assert _confirm(api, headers, payment_id).get_json()["paymentStatus"] == "approved"

    assert cut(api, headers, attempt["id"])["canContinue"] is True
    response = continue_(api, headers, attempt["id"])
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["id"] == attempt["id"]
    db_session.expire_all()
    assert db_session.get(TestAttempt, uuid.UUID(attempt["id"])).tier.value == "paid_full"
    assert cut(api, headers, attempt["id"])["servedItems"] == 90


def test_a_second_payment_while_active_extends_the_period(api, person, payments, db_session):
    user, headers = person
    first = payments.add_payment(external_reference=user["id"], amount=PRICE)
    second = payments.add_payment(external_reference=user["id"], amount=PRICE)
    end_1 = datetime.fromisoformat(_confirm(api, headers, first.id).get_json()["currentPeriodEnd"])
    end_2 = datetime.fromisoformat(_confirm(api, headers, second.id).get_json()["currentPeriodEnd"])
    assert end_2 - end_1 == timedelta(days=30)


def test_the_webhook_secret_never_reaches_a_log_line(api, person, payments, webhook_secret, captured_logs):
    user, headers = person
    payment = payments.add_payment(external_reference=user["id"], amount=PRICE)
    _confirm(api, headers, payment.id)
    _notify(api, payment.id)
    assert not any(SECRET in line for line in captured_logs)
