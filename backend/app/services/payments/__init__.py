from app.services.payments.base import CheckoutRequest, PaymentGateway, RemotePayment
from app.services.payments.local import LocalPaymentGateway
from app.services.payments.mercadopago import MercadoPagoGateway

__all__ = [
    "CheckoutRequest",
    "LocalPaymentGateway",
    "MercadoPagoGateway",
    "PaymentGateway",
    "RemotePayment",
    "build_payment_gateway",
]


def build_payment_gateway(config) -> PaymentGateway:
    if config.PAYMENT_PROVIDER == "mercadopago":
        return MercadoPagoGateway(config.MERCADOPAGO_ACCESS_TOKEN)
    return LocalPaymentGateway()
