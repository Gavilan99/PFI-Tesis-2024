import os

from flask import Flask

from app.blueprints.attempts import attempts_bp
from app.blueprints.auth import auth_bp
from app.blueprints.core import core_bp
from app.blueprints.users import users_bp
from app.config import ConfigError, get_config, load_env_file
from app.errors import register_error_handlers
from app.extensions import cors, init_db
from app.logging_config import configure_logging
from app.security import init_auth
from app.services.identity import LocalIdentityProvider, build_identity_provider


def create_app(config_name: str | None = None) -> Flask:
    load_env_file(config_name)
    config_name = config_name or os.environ.get("APP_ENV", "development")
    config = get_config(config_name)

    identity = build_identity_provider(config)
    # Config already refuses this; checked again on the object actually built.
    if config_name == "production" and isinstance(identity, LocalIdentityProvider):
        raise ConfigError("El proveedor de identidad local no se puede usar en producción.")

    # A JSON API: no static files, so no `/static` route either.
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config)
    app.extensions["identity_provider"] = identity

    configure_logging(app)
    init_db(app)
    cors.init_app(app, origins=config.CORS_ALLOWED_ORIGINS)
    register_error_handlers(app)
    init_auth(app)

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(attempts_bp)

    return app
