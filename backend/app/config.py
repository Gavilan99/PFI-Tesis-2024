import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy.engine import URL

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class ConfigError(RuntimeError):
    pass


def load_env_file(env_name: str | None = None) -> None:
    """Load backend/.env for local runs. Variables already in the environment win.

    Skipped for production: there, only what the platform injects is read.
    """
    if (env_name or os.environ.get("APP_ENV", "development")) == "production":
        return
    load_dotenv(ENV_FILE, override=False)


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"Falta la variable de entorno obligatoria: {name}")
    return value


def _split_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


IDENTITY_PROVIDERS = ("cognito", "local")
MAIL_SENDERS = ("ses", "local")
PAYMENT_PROVIDERS = ("mercadopago", "local")
TEXT_GENERATORS = ("bedrock", "local")
DEFAULT_BEDROCK_MODEL_ID = "amazon.nova-lite-v1:0"
# The individual plan outside production when nothing is set. EXAMPLE VALUES: the real price and period
# come from the business model, which is not closed yet. Production has no default (`_set_plan`).
EXAMPLE_PLAN_PRICE = "4999.00"
EXAMPLE_PLAN_DAYS = 30
PLAN_CURRENCIES = ("ARS",)
LOCAL_FRONTEND_BASE_URL = "http://localhost:4200"
# The two return URLs Mercado Pago can send the buyer back to: the frontend's screen, or the backend's
# redirect to it (for when the frontend is on localhost, which Mercado Pago does not accept).
FRONTEND_RETURN_PATH = "/pago"
API_RETURN_PATH = "/api/payments/return"
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
LOCAL_CONTACT_MAIL_TO = "contacto@nureon.invalid"
# What development and test record as the accepted version when CONSENT_VERSION is not set.
LOCAL_CONSENT_VERSION = "local"
CONSENT_VERSION_MAX_LENGTH = 32

def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} tiene que ser un número entero; vale '{raw}'.") from None
    if value <= 0:
        raise ConfigError(f"{name} tiene que ser mayor que cero; vale {value}.")
    return value


def _non_negative_int(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} tiene que ser un número entero; vale '{raw}'.") from None
    if value < 0:
        raise ConfigError(f"{name} no puede ser negativo; vale {value}.")
    return value


DATABASE_PARTS = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")


def _production_database_url() -> str:
    """DATABASE_URL if given; otherwise built from its parts.

    In AWS the password is the RDS-managed master secret, injected by ECS key by key (DB_USER,
    DB_PASSWORD), so there is no single URL to inject. URL.create escapes whatever the password holds.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    present = [name for name in DATABASE_PARTS if os.environ.get(name)]
    if not present:
        raise ConfigError(
            "Falta la variable de entorno obligatoria: DATABASE_URL "
            f"(o sus partes: {', '.join(DATABASE_PARTS)})."
        )
    missing = [name for name in DATABASE_PARTS if name not in present]
    if missing:
        raise ConfigError(
            "Sin DATABASE_URL, la conexión se arma por partes y faltan: " + ", ".join(missing) + "."
        )
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=_positive_int("DB_PORT", 5432),
        database=os.environ["DB_NAME"],
        # RDS accepts TLS; a local Postgres for the production compose sets DB_SSLMODE=disable.
        query={"sslmode": os.environ.get("DB_SSLMODE", "require").strip()},
    ).render_as_string(hide_password=False)


def _development_database_url() -> str:
    return os.environ.get("DATABASE_URL", "postgresql+psycopg://nureon:nureon@localhost:5433/nureon_dev")


def _test_database_url() -> str:
    # Never falls back to DATABASE_URL: a dev .env must not send the suite to the dev database.
    return os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://nureon:nureon@localhost:5433/nureon_test")


_DATABASE_URLS = {
    "development": _development_database_url,
    "test": _test_database_url,
    "production": _production_database_url,
}


def database_url(env_name: str) -> str:
    """Only the database URL of an environment, without the rest of its configuration.

    What the migrations read. A one-off migration task can run the new image with the service's
    current environment, before the new code is deployed (deploy-runbook.md): it must not fail
    because a setting the new code requires, and the old environment lacks, is missing.
    """
    try:
        return _DATABASE_URLS[env_name]()
    except KeyError:
        valid = ", ".join(_DATABASE_URLS)
        raise ConfigError(f"Entorno desconocido: '{env_name}'. Opciones válidas: {valid}") from None


def _consent_version(default: str | None) -> str:
    """The version of the privacy policy and terms in force, stored with every new account."""
    value = os.environ.get("CONSENT_VERSION", "").strip() or default
    if not value:
        raise ConfigError("Falta la variable de entorno obligatoria: CONSENT_VERSION")
    if len(value) > CONSENT_VERSION_MAX_LENGTH:
        raise ConfigError(
            f"CONSENT_VERSION puede tener hasta {CONSENT_VERSION_MAX_LENGTH} caracteres; tiene {len(value)}."
        )
    return value


def _mail_sender(default: str) -> str:
    name = os.environ.get("MAIL_SENDER", default).strip().lower()
    if name not in MAIL_SENDERS:
        valid = ", ".join(MAIL_SENDERS)
        raise ConfigError(f"MAIL_SENDER desconocido: '{name}'. Opciones válidas: {valid}")
    return name


def _payment_provider(default: str) -> str:
    name = os.environ.get("PAYMENT_PROVIDER", default).strip().lower()
    if name not in PAYMENT_PROVIDERS:
        valid = ", ".join(PAYMENT_PROVIDERS)
        raise ConfigError(f"PAYMENT_PROVIDER desconocido: '{name}'. Opciones válidas: {valid}")
    return name


def _plan_price(default: str | None) -> Decimal:
    raw = os.environ.get("PLAN_INDIVIDUAL_PRICE", "").strip() or default
    if not raw:
        raise ConfigError("Falta la variable de entorno obligatoria: PLAN_INDIVIDUAL_PRICE")
    try:
        price = Decimal(raw)
    except InvalidOperation:
        raise ConfigError(f"PLAN_INDIVIDUAL_PRICE tiene que ser un número (p. ej. 4999.00); vale '{raw}'.") from None
    if not price.is_finite() or price <= 0 or price != price.quantize(Decimal("0.01")):
        raise ConfigError(
            f"PLAN_INDIVIDUAL_PRICE tiene que ser mayor que cero y con hasta dos decimales; vale '{raw}'."
        )
    return price.quantize(Decimal("0.01"))


def _base_url(name: str, default: str | None) -> str:
    value = (os.environ.get(name, "").strip() or default or "").rstrip("/")
    if not value:
        raise ConfigError(f"Falta la variable de entorno obligatoria: {name}")
    if not value.startswith(("https://", "http://")):
        raise ConfigError(f"{name} tiene que empezar con https:// o http://; vale '{value}'.")
    return value


def _is_local(url: str) -> bool:
    return (urlsplit(url).hostname or "") in _LOCAL_HOSTS


def _identity_provider(default: str) -> str:
    name = os.environ.get("IDENTITY_PROVIDER", default).strip().lower()
    if name not in IDENTITY_PROVIDERS:
        valid = ", ".join(IDENTITY_PROVIDERS)
        raise ConfigError(f"IDENTITY_PROVIDER desconocido: '{name}'. Opciones válidas: {valid}")
    return name


def _text_generator(default: str) -> str:
    name = os.environ.get("TEXT_GENERATOR", default).strip().lower()
    if name not in TEXT_GENERATORS:
        valid = ", ".join(TEXT_GENERATORS)
        raise ConfigError(f"TEXT_GENERATOR desconocido: '{name}'. Opciones válidas: {valid}")
    return name


class BaseConfig:
    TESTING = False
    DEBUG = False
    PROPAGATE_EXCEPTIONS = False

    def __init__(self) -> None:
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
        self.CORS_ALLOWED_ORIGINS = _split_origins(
            os.environ.get("CORS_ALLOWED_ORIGINS", "")
        )
        self.COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-2")
        self.COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
        self.COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "")

        # The personalized description of the paid plan's result (Feature 17): which generator writes
        # it, the Bedrock model it asks for, and how long it waits for an answer. The provider is
        # chosen per environment (`_set_text_generator`), like identity, mail and payments.
        self.TEXT_GENERATOR = "local"
        self.BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-2")
        self.BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "").strip() or DEFAULT_BEDROCK_MODEL_ID
        self.TEXT_GENERATION_TIMEOUT_SECONDS = _positive_int("TEXT_GENERATION_TIMEOUT_SECONDS", 10)

        self.AWS_PROFILE = os.environ.get("AWS_PROFILE") or None

        # Which classifier closes an attempt: stub | legacy_tree | trained. Validated when the app is
        # created (app.ml.registry), where the backends are known.
        self.CLASSIFIER_BACKEND = os.environ.get("CLASSIFIER_BACKEND", "stub").strip().lower()
        # The training's output: the cut plan (manifest.json, precision_by_items.json), which every
        # backend serves by, and the twelve models `trained` loads. Unset, app/ml/artifacts/.
        self.CLASSIFIER_ARTIFACTS_DIR = os.environ.get("CLASSIFIER_ARTIFACTS_DIR") or None

        # The contact form: mailed to CONTACT_MAIL_TO, never stored. The sender is chosen per
        # environment (`_set_mail_sender`); the addresses are only required with SES.
        self.MAIL_SENDER = "local"
        self.SES_REGION = os.environ.get("SES_REGION", "us-east-2")
        # With the local double nothing is sent, so a placeholder will do; SES requires the real one.
        self.CONTACT_MAIL_TO = os.environ.get("CONTACT_MAIL_TO", "").strip() or LOCAL_CONTACT_MAIL_TO
        self.CONTACT_MAIL_FROM = os.environ.get("CONTACT_MAIL_FROM", "").strip() or self.CONTACT_MAIL_TO
        # The contact route is public: at most this many messages per origin per window.
        self.CONTACT_RATE_LIMIT = _positive_int("CONTACT_RATE_LIMIT", 5)
        self.CONTACT_RATE_WINDOW_SECONDS = _positive_int("CONTACT_RATE_WINDOW_SECONDS", 3600)
        # Proxies in front of the app whose X-Forwarded-For entry is trusted. 0 locally: no proxy,
        # and the header is whatever the client wrote. Production sets its own default.
        self.TRUSTED_PROXY_HOPS = _non_negative_int("TRUSTED_PROXY_HOPS", 0)
        # An account in the identity provider without its `users` row gets the row on its first
        # authenticated request. Production sets False: every account there comes from the registration,
        # with its consent (Feature 11).
        self.PROVISION_MISSING_ACCOUNTS = True

        # Payments (Feature 6): one payment through Mercado Pago Checkout Pro buys the individual plan
        # for PLAN_INDIVIDUAL_DAYS. The provider is chosen per environment (`_set_payment_provider`), the
        # plan too (`_set_plan`). The access token and the webhook secret never leave the backend.
        self.PAYMENT_PROVIDER = "local"
        self.MERCADOPAGO_ACCESS_TOKEN = ""
        self.MERCADOPAGO_WEBHOOK_SECRET = ""
        # Where Mercado Pago sends the buyer back: the frontend's /pago. Mercado Pago does not accept
        # localhost there, so with the frontend on localhost PUBLIC_API_BASE_URL (a tunnel to this
        # backend) is set, and the return goes through the backend's redirect (/api/payments/return).
        self.FRONTEND_BASE_URL = LOCAL_FRONTEND_BASE_URL
        self.PUBLIC_API_BASE_URL = None
        self.PAYMENT_RETURN_URL = LOCAL_FRONTEND_BASE_URL + FRONTEND_RETURN_PATH

    def _set_plan(self, *, price_default: str | None, days_default: int | None) -> None:
        self.PLAN_INDIVIDUAL_PRICE = _plan_price(price_default)
        if days_default is None and not os.environ.get("PLAN_INDIVIDUAL_DAYS", "").strip():
            raise ConfigError("Falta la variable de entorno obligatoria: PLAN_INDIVIDUAL_DAYS")
        self.PLAN_INDIVIDUAL_DAYS = _positive_int("PLAN_INDIVIDUAL_DAYS", days_default or 0)
        self.PLAN_INDIVIDUAL_CURRENCY = os.environ.get("PLAN_INDIVIDUAL_CURRENCY", "ARS").strip().upper()
        if self.PLAN_INDIVIDUAL_CURRENCY not in PLAN_CURRENCIES:
            valid = ", ".join(PLAN_CURRENCIES)
            raise ConfigError(
                f"PLAN_INDIVIDUAL_CURRENCY desconocida: '{self.PLAN_INDIVIDUAL_CURRENCY}'. Opciones válidas: {valid}"
            )

    def _set_payment_provider(self, default: str, *, frontend_required: bool) -> None:
        self.PAYMENT_PROVIDER = _payment_provider(default)
        self.FRONTEND_BASE_URL = _base_url(
            "FRONTEND_BASE_URL", None if frontend_required else LOCAL_FRONTEND_BASE_URL
        )
        self.PUBLIC_API_BASE_URL = (
            _base_url("PUBLIC_API_BASE_URL", None) if os.environ.get("PUBLIC_API_BASE_URL", "").strip() else None
        )
        self.PAYMENT_RETURN_URL = (
            self.PUBLIC_API_BASE_URL + API_RETURN_PATH
            if self.PUBLIC_API_BASE_URL
            else self.FRONTEND_BASE_URL + FRONTEND_RETURN_PATH
        )
        if self.PAYMENT_PROVIDER != "mercadopago":
            return
        self.MERCADOPAGO_ACCESS_TOKEN = _require("MERCADOPAGO_ACCESS_TOKEN").strip()
        self.MERCADOPAGO_WEBHOOK_SECRET = _require("MERCADOPAGO_WEBHOOK_SECRET").strip()
        if _is_local(self.PAYMENT_RETURN_URL):
            raise ConfigError(
                "Mercado Pago no acepta localhost como URL de retorno: con FRONTEND_BASE_URL en localhost, "
                "PUBLIC_API_BASE_URL tiene que ser la URL pública de este backend (p. ej. un túnel)."
            )

    def _check_aws_profile(self, *, profile_required: bool) -> None:
        # The `default` profile of a developer machine can hold full access to the account: boto3
        # gets the profile from here, explicitly, and never falls back to it.
        if self.AWS_PROFILE == "default":
            raise ConfigError(
                "AWS_PROFILE=default no está permitido: usá el perfil del proyecto (p. ej. nureon)."
            )
        if profile_required and not self.AWS_PROFILE:
            raise ConfigError("Falta la variable de entorno obligatoria: AWS_PROFILE")

    def _set_identity_provider(self, default: str, *, profile_required: bool) -> None:
        self.IDENTITY_PROVIDER = _identity_provider(default)
        if self.IDENTITY_PROVIDER != "cognito":
            return
        self.COGNITO_USER_POOL_ID = _require("COGNITO_USER_POOL_ID")
        self.COGNITO_APP_CLIENT_ID = _require("COGNITO_APP_CLIENT_ID")
        self._check_aws_profile(profile_required=profile_required)

    def _set_mail_sender(self, default: str, *, profile_required: bool) -> None:
        self.MAIL_SENDER = _mail_sender(default)
        if self.MAIL_SENDER != "ses":
            return
        self.CONTACT_MAIL_TO = _require("CONTACT_MAIL_TO").strip()
        # In the SES sandbox the sender must be a verified identity too: the inbox itself is the default.
        self.CONTACT_MAIL_FROM = os.environ.get("CONTACT_MAIL_FROM", "").strip() or self.CONTACT_MAIL_TO
        self._check_aws_profile(profile_required=profile_required)

    def _set_text_generator(self, default: str, *, profile_required: bool) -> None:
        self.TEXT_GENERATOR = _text_generator(default)
        if self.TEXT_GENERATOR != "bedrock":
            return
        self._check_aws_profile(profile_required=profile_required)


class DevelopmentConfig(BaseConfig):
    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
        self.CONSENT_VERSION = _consent_version(LOCAL_CONSENT_VERSION)
        self.SQLALCHEMY_DATABASE_URI = _development_database_url()
        if not self.CORS_ALLOWED_ORIGINS:
            self.CORS_ALLOWED_ORIGINS = ["http://localhost:4200"]
        self._set_identity_provider(default="local", profile_required=True)
        self._set_mail_sender(default="local", profile_required=True)
        self._set_text_generator(default="local", profile_required=True)
        self._set_plan(price_default=EXAMPLE_PLAN_PRICE, days_default=EXAMPLE_PLAN_DAYS)
        self._set_payment_provider(default="local", frontend_required=False)


class TestConfig(BaseConfig):
    TESTING = True

    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key")
        # Fixed, whatever a developer's .env says: the suite checks what gets stored.
        self.CONSENT_VERSION = LOCAL_CONSENT_VERSION
        self.SQLALCHEMY_DATABASE_URI = _test_database_url()
        if not self.CORS_ALLOWED_ORIGINS:
            self.CORS_ALLOWED_ORIGINS = ["http://localhost:4200"]
        # The suite never talks to AWS, whatever a developer's .env selects.
        self.IDENTITY_PROVIDER = "local"
        self.MAIL_SENDER = "local"
        self.TEXT_GENERATOR = "local"
        # Nor sees a real inbox: a developer's .env may hold one.
        self.CONTACT_MAIL_TO = self.CONTACT_MAIL_FROM = LOCAL_CONTACT_MAIL_TO
        # Nor Mercado Pago, nor a developer's plan or tunnel: the example plan and the local URLs, fixed.
        self.PAYMENT_PROVIDER = "local"
        self.PLAN_INDIVIDUAL_PRICE = Decimal(EXAMPLE_PLAN_PRICE)
        self.PLAN_INDIVIDUAL_DAYS = EXAMPLE_PLAN_DAYS
        self.PLAN_INDIVIDUAL_CURRENCY = "ARS"


class ProductionConfig(BaseConfig):
    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = _require("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = _production_database_url()
        # Not a setting: a row created on login would be an account without consent.
        self.PROVISION_MISSING_ACCOUNTS = False
        # Exactly one hop: the ALB that Express Mode puts in front of the service, which appends the
        # visitor's address. Anything before it in the header was written by the client.
        self.TRUSTED_PROXY_HOPS = _non_negative_int("TRUSTED_PROXY_HOPS", 1)
        if not self.CORS_ALLOWED_ORIGINS:
            raise ConfigError(
                "Falta la variable de entorno obligatoria: CORS_ALLOWED_ORIGINS"
            )
        # Deployed, the classifier is chosen on purpose: a default would put the stub in front of
        # users without anyone deciding it.
        self.CLASSIFIER_BACKEND = _require("CLASSIFIER_BACKEND").strip().lower()
        if _identity_provider(default="cognito") == "local":
            raise ConfigError(
                "IDENTITY_PROVIDER=local es un doble para tests y desarrollo: "
                "no se puede usar en producción."
            )
        # Deployed, credentials come from the platform's role, not from a profile file.
        self._set_identity_provider(default="cognito", profile_required=False)
        if _mail_sender(default="ses") == "local":
            raise ConfigError(
                "MAIL_SENDER=local es un doble para tests y desarrollo: no se puede usar en producción."
            )
        self._set_mail_sender(default="ses", profile_required=False)
        if _text_generator(default="bedrock") == "local":
            raise ConfigError(
                "TEXT_GENERATOR=local es un doble para tests y desarrollo: no se puede usar en producción."
            )
        self._set_text_generator(default="bedrock", profile_required=False)
        # Which text the people registering accept is chosen on purpose, like the classifier.
        self.CONSENT_VERSION = _consent_version(None)
        # And what the plan costs and lasts: no example value can reach a real payment.
        self._set_plan(price_default=None, days_default=None)
        if _payment_provider(default="mercadopago") == "local":
            raise ConfigError(
                "PAYMENT_PROVIDER=local es un doble para tests y desarrollo: no se puede usar en producción."
            )
        self._set_payment_provider(default="mercadopago", frontend_required=True)


_CONFIGS = {
    "development": DevelopmentConfig,
    "test": TestConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str) -> BaseConfig:
    try:
        config_class = _CONFIGS[env_name]
    except KeyError:
        valid = ", ".join(_CONFIGS)
        raise ConfigError(f"Entorno desconocido: '{env_name}'. Opciones válidas: {valid}")
    return config_class()
