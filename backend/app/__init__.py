import os

from flask import Flask

from app.blueprints.core import core_bp
from app.config import get_config
from app.errors import register_error_handlers
from app.extensions import cors, init_db
from app.logging_config import configure_logging


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("APP_ENV", "development")
    config = get_config(config_name)

    app = Flask(__name__)
    app.config.from_object(config)

    configure_logging(app)
    init_db(app)
    cors.init_app(app, origins=config.CORS_ALLOWED_ORIGINS)
    register_error_handlers(app)

    app.register_blueprint(core_bp)

    return app
