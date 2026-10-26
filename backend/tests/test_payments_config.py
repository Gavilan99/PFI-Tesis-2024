"""Selecting the payment gateway and the plan. The local double is not a production mode, and no
example price can reach production."""

from decimal import Decimal

import pytest

from app import create_app
from app.config import ConfigError, get_config
from app.services.payments import LocalPaymentGateway, MercadoPagoGateway, build_payment_gateway
from tests.production_env import set_production_env


@pytest.fixture()
def production_env(monkeypatch):
    set_production_env(monkeypatch)


def test_production_defaults_to_mercado_pago_with_the_configured_plan(production_env):
    config = get_config("production")
    assert config.PAYMENT_PROVIDER == "mercadopago"
    # Straight back to the frontend (HTTPS, not localhost): no tunnel, no redirect.
    assert config.PAYMENT_RETURN_URL == "https://nureon.example/pago"
    assert (config.PLAN_INDIVIDUAL_PRICE, config.PLAN_INDIVIDUAL_CURRENCY, config.PLAN_INDIVIDUAL_DAYS) == (
        Decimal("1234.50"), "ARS", 31,
    )
    assert isinstance(build_payment_gateway(config), MercadoPagoGateway)


def test_production_refuses_to_start_with_the_local_double(production_env, monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "local")
    with pytest.raises(ConfigError, match="PAYMENT_PROVIDER=local"):
        create_app("production")


@pytest.mark.parametrize("name", [
    "MERCADOPAGO_ACCESS_TOKEN", "MERCADOPAGO_WEBHOOK_SECRET", "FRONTEND_BASE_URL",
    "PLAN_INDIVIDUAL_PRICE", "PLAN_INDIVIDUAL_DAYS",
])
def test_production_requires(production_env, monkeypatch, name):
    monkeypatch.delenv(name)
    with pytest.raises(ConfigError, match=name):
        get_config("production")


@pytest.mark.parametrize("price", ["0", "-1", "abc", "10.999", "NaN"])
def test_a_price_must_be_positive_with_two_decimals_at_most(production_env, monkeypatch, price):
    monkeypatch.setenv("PLAN_INDIVIDUAL_PRICE", price)
    with pytest.raises(ConfigError, match="PLAN_INDIVIDUAL_PRICE"):
        get_config("production")


def test_an_unknown_currency_fails(production_env, monkeypatch):
    monkeypatch.setenv("PLAN_INDIVIDUAL_CURRENCY", "USD")
    with pytest.raises(ConfigError, match="PLAN_INDIVIDUAL_CURRENCY"):
        get_config("production")


def test_unknown_payment_provider_fails(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "stripe")
    with pytest.raises(ConfigError, match="PAYMENT_PROVIDER desconocido"):
        get_config("development")


def test_development_defaults_to_the_local_double_and_the_example_plan(monkeypatch):
    for name in ("PAYMENT_PROVIDER", "PLAN_INDIVIDUAL_PRICE", "PLAN_INDIVIDUAL_DAYS", "PLAN_INDIVIDUAL_CURRENCY"):
        monkeypatch.delenv(name, raising=False)
    config = get_config("development")
    assert config.PAYMENT_PROVIDER == "local"
    assert (config.PLAN_INDIVIDUAL_PRICE, config.PLAN_INDIVIDUAL_DAYS) == (Decimal("4999.00"), 30)
    assert isinstance(build_payment_gateway(config), LocalPaymentGateway)


@pytest.fixture()
def development_mercadopago_env(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "mercadopago")
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "x")
    monkeypatch.setenv("MERCADOPAGO_WEBHOOK_SECRET", "y")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:4200")
    monkeypatch.delenv("PUBLIC_API_BASE_URL", raising=False)


def test_mercado_pago_refuses_a_localhost_return(development_mercadopago_env):
    # Mercado Pago does not accept localhost in back_urls: the frontend on localhost needs the tunnel.
    with pytest.raises(ConfigError, match="PUBLIC_API_BASE_URL"):
        get_config("development")


def test_with_a_tunnel_the_return_goes_through_the_backend(development_mercadopago_env, monkeypatch):
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://algo.trycloudflare.com/")
    config = get_config("development")
    assert config.PAYMENT_RETURN_URL == "https://algo.trycloudflare.com/api/payments/return"


def test_without_mercado_pago_the_return_is_the_local_frontend(monkeypatch):
    for name in ("PAYMENT_PROVIDER", "PUBLIC_API_BASE_URL", "FRONTEND_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    assert get_config("development").PAYMENT_RETURN_URL == "http://localhost:4200/pago"


def test_the_test_suite_never_talks_to_mercado_pago(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "mercadopago")
    monkeypatch.setenv("PLAN_INDIVIDUAL_PRICE", "1.00")
    config = get_config("test")
    assert config.PAYMENT_PROVIDER == "local"
    assert config.PLAN_INDIVIDUAL_PRICE == Decimal("4999.00")
