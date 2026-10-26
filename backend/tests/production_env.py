"""What production requires of payments (Feature 6), for the tests that build a production config.

Every such test sets its own environment; they all add these on top, so a production config can be
built at all. The values are placeholders: nothing here reaches Mercado Pago.
"""

PAYMENT_ENV = {
    "MERCADOPAGO_ACCESS_TOKEN": "APP_USR-placeholder",
    "MERCADOPAGO_WEBHOOK_SECRET": "placeholder-secret",
    "FRONTEND_BASE_URL": "https://nureon.example",
    "PLAN_INDIVIDUAL_PRICE": "1234.50",
    "PLAN_INDIVIDUAL_DAYS": "31",
}


def set_payment_env(monkeypatch) -> None:
    # Production returns the buyer straight to the frontend: no PUBLIC_API_BASE_URL.
    monkeypatch.delenv("PUBLIC_API_BASE_URL", raising=False)
    monkeypatch.delenv("PAYMENT_PROVIDER", raising=False)
    monkeypatch.delenv("PLAN_INDIVIDUAL_CURRENCY", raising=False)
    for name, value in PAYMENT_ENV.items():
        monkeypatch.setenv(name, value)


def set_production_env(monkeypatch) -> None:
    """A whole production environment that builds: the rest of production's requirements too."""
    for name, value in {
        "SECRET_KEY": "x",
        "DATABASE_URL": "postgresql+psycopg://u:p@host/db",
        "CORS_ALLOWED_ORIGINS": "https://nureon.example",
        "COGNITO_USER_POOL_ID": "us-east-2_example",
        "COGNITO_APP_CLIENT_ID": "exampleclientid",
        "CLASSIFIER_BACKEND": "stub",
        "CONTACT_MAIL_TO": "contacto@nureon.example",
        "CONSENT_VERSION": "2026-10-20",
    }.items():
        monkeypatch.setenv(name, value)
    for name in ("IDENTITY_PROVIDER", "MAIL_SENDER", "AWS_PROFILE", "CONTACT_MAIL_FROM"):
        monkeypatch.delenv(name, raising=False)
    set_payment_env(monkeypatch)
