import os
from pathlib import Path

from dotenv import load_dotenv

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
LOCAL_CONTACT_MAIL_TO = "contacto@nureon.invalid"

# The subset is balanced across the four grouping systems, so its size must split evenly among them.
GROUPING_SYSTEM_COUNT = 4


def _subset_size(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        size = int(raw)
    except ValueError:
        raise ConfigError(f"{name} tiene que ser un número entero; vale '{raw}'.") from None
    if size <= 0 or size % GROUPING_SYSTEM_COUNT:
        raise ConfigError(
            f"{name} tiene que ser un múltiplo positivo de {GROUPING_SYSTEM_COUNT}, "
            f"para repartirse en partes iguales entre los sistemas de agrupamiento; vale {size}."
        )
    return size


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} tiene que ser un número entero; vale '{raw}'.") from None
    if value <= 0:
        raise ConfigError(f"{name} tiene que ser mayor que cero; vale {value}.")
    return value


def _mail_sender(default: str) -> str:
    name = os.environ.get("MAIL_SENDER", default).strip().lower()
    if name not in MAIL_SENDERS:
        valid = ", ".join(MAIL_SENDERS)
        raise ConfigError(f"MAIL_SENDER desconocido: '{name}'. Opciones válidas: {valid}")
    return name


def _identity_provider(default: str) -> str:
    name = os.environ.get("IDENTITY_PROVIDER", default).strip().lower()
    if name not in IDENTITY_PROVIDERS:
        valid = ", ".join(IDENTITY_PROVIDERS)
        raise ConfigError(f"IDENTITY_PROVIDER desconocido: '{name}'. Opciones válidas: {valid}")
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

        self.AWS_PROFILE = os.environ.get("AWS_PROFILE") or None

        # Questions served per attempt tier, split evenly across the grouping systems.
        self.SUBSET_SIZE_FREE_REDUCED = _subset_size("SUBSET_SIZE_FREE_REDUCED", 20)
        self.SUBSET_SIZE_PAID_FULL = _subset_size("SUBSET_SIZE_PAID_FULL", 60)

        # Which classifier closes an attempt: stub | legacy_tree | trained. Validated when the app is
        # created (app.ml.registry), where the backends are known.
        self.CLASSIFIER_BACKEND = os.environ.get("CLASSIFIER_BACKEND", "stub").strip().lower()
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


class DevelopmentConfig(BaseConfig):
    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
        self.SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nureon:nureon@localhost:5433/nureon_dev",
        )
        if not self.CORS_ALLOWED_ORIGINS:
            self.CORS_ALLOWED_ORIGINS = ["http://localhost:4200"]
        self._set_identity_provider(default="local", profile_required=True)
        self._set_mail_sender(default="local", profile_required=True)


class TestConfig(BaseConfig):
    TESTING = True

    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key")
        # Never falls back to DATABASE_URL: a dev .env must not send the suite to the dev database.
        self.SQLALCHEMY_DATABASE_URI = os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+psycopg://nureon:nureon@localhost:5433/nureon_test",
        )
        if not self.CORS_ALLOWED_ORIGINS:
            self.CORS_ALLOWED_ORIGINS = ["http://localhost:4200"]
        # The suite never talks to AWS, whatever a developer's .env selects.
        self.IDENTITY_PROVIDER = "local"
        self.MAIL_SENDER = "local"
        # Nor sees a real inbox: a developer's .env may hold one.
        self.CONTACT_MAIL_TO = self.CONTACT_MAIL_FROM = LOCAL_CONTACT_MAIL_TO


class ProductionConfig(BaseConfig):
    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = _require("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = _require("DATABASE_URL")
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
