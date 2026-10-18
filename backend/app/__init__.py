import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.blueprints.attempts import attempts_bp
from app.blueprints.auth import auth_bp
from app.blueprints.core import core_bp
from app.blueprints.feedback import feedback_bp
from app.blueprints.results import results_bp
from app.blueprints.users import users_bp
from app.config import ConfigError, get_config, load_env_file
from app.errors import register_error_handlers
from app.extensions import cors, init_db
from app.logging_config import configure_logging
from app.ml.cut_plan import load_cut_plan
from app.ml.registry import build_classifier
from app.security import init_auth
from app.services.identity import LocalIdentityProvider, build_identity_provider
from app.services.mail import LocalMailSender, build_mail_sender
from app.services.rate_limit import SlidingWindowLimiter


def create_app(config_name: str | None = None) -> Flask:
    load_env_file(config_name)
    config_name = config_name or os.environ.get("APP_ENV", "development")
    config = get_config(config_name)

    identity = build_identity_provider(config)
    # Before anything else is set up: an invalid cut plan or a backend that cannot run stops the app
    # here, by name.
    cut_plan = load_cut_plan(config)
    if config_name == "production" and cut_plan.synthetic:
        raise ConfigError(
            f"Los artefactos de {cut_plan.directory} son sintéticos ({cut_plan.model_version}): sirven para "
            "desarrollo y tests, no son un modelo. En producción la app no arranca con ellos: la imagen "
            "se construye con los artefactos reales."
        )
    classifier = build_classifier(config)
    # Config already refuses this; checked again on the object actually built.
    if config_name == "production" and isinstance(identity, LocalIdentityProvider):
        raise ConfigError("El proveedor de identidad local no se puede usar en producción.")
    mail_sender = build_mail_sender(config)
    if config_name == "production" and isinstance(mail_sender, LocalMailSender):
        raise ConfigError("El envío de mail local no se puede usar en producción.")

    # A JSON API: no static files, so no `/static` route either.
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config)
    if config.TRUSTED_PROXY_HOPS:
        # Only X-Forwarded-For, and only the last N entries: the ones our proxies appended. Host,
        # scheme, port and prefix headers are left alone; nothing here reads them.
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=config.TRUSTED_PROXY_HOPS, x_proto=0, x_host=0, x_port=0, x_prefix=0
        )
    app.extensions["identity_provider"] = identity
    app.extensions["cut_plan"] = cut_plan
    app.extensions["classifier"] = classifier
    app.extensions["mail_sender"] = mail_sender
    app.extensions["contact_rate_limiter"] = SlidingWindowLimiter(
        config.CONTACT_RATE_LIMIT, config.CONTACT_RATE_WINDOW_SECONDS
    )

    configure_logging(app)
    app.logger.info("Classifier backend: %s (%s)", config.CLASSIFIER_BACKEND, classifier.model_version)
    init_db(app)
    cors.init_app(app, origins=config.CORS_ALLOWED_ORIGINS)
    register_error_handlers(app)
    init_auth(app)

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(attempts_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(feedback_bp)

    return app
