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
        self.COGNITO_REGION = os.environ.get("COGNITO_REGION", "sa-east-1")
        self.COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
        self.COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "")

    def _set_identity_provider(self, default: str) -> None:
        self.IDENTITY_PROVIDER = _identity_provider(default)
        if self.IDENTITY_PROVIDER == "cognito":
            self.COGNITO_USER_POOL_ID = _require("COGNITO_USER_POOL_ID")
            self.COGNITO_APP_CLIENT_ID = _require("COGNITO_APP_CLIENT_ID")


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
        self._set_identity_provider(default="local")


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


class ProductionConfig(BaseConfig):
    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = _require("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = _require("DATABASE_URL")
        if not self.CORS_ALLOWED_ORIGINS:
            raise ConfigError(
                "Falta la variable de entorno obligatoria: CORS_ALLOWED_ORIGINS"
            )
        if _identity_provider(default="cognito") == "local":
            raise ConfigError(
                "IDENTITY_PROVIDER=local es un doble para tests y desarrollo: "
                "no se puede usar en producción."
            )
        self._set_identity_provider(default="cognito")


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
