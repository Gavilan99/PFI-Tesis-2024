"""Selecting the text generator for personalized descriptions (Feature 17). The local double is not
a production mode, like identity, mail and payments."""

import pytest

from app import create_app
from app.config import ConfigError, get_config
from app.services.text_generation import BedrockTextGenerator, LocalTextGenerator, build_text_generator
from tests.production_env import set_production_env


@pytest.fixture()
def production_env(monkeypatch):
    set_production_env(monkeypatch)
    monkeypatch.delenv("TEXT_GENERATOR", raising=False)


def test_production_defaults_to_bedrock_with_the_configured_model(production_env):
    config = get_config("production")
    assert config.TEXT_GENERATOR == "bedrock"
    assert config.BEDROCK_MODEL_ID == "amazon.nova-lite-v1:0"
    assert isinstance(build_text_generator(config), BedrockTextGenerator)


def test_production_refuses_to_start_with_the_local_double(production_env, monkeypatch):
    monkeypatch.setenv("TEXT_GENERATOR", "local")
    with pytest.raises(ConfigError, match="TEXT_GENERATOR=local"):
        create_app("production")


def test_unknown_text_generator_fails(monkeypatch):
    monkeypatch.setenv("TEXT_GENERATOR", "openai")
    with pytest.raises(ConfigError, match="TEXT_GENERATOR desconocido"):
        get_config("development")


def test_development_defaults_to_the_local_double(monkeypatch):
    monkeypatch.delenv("TEXT_GENERATOR", raising=False)
    config = get_config("development")
    assert config.TEXT_GENERATOR == "local"
    assert isinstance(build_text_generator(config), LocalTextGenerator)


def test_development_with_bedrock_needs_an_explicit_profile_and_never_default(monkeypatch):
    monkeypatch.setenv("IDENTITY_PROVIDER", "local")
    monkeypatch.setenv("MAIL_SENDER", "local")
    monkeypatch.setenv("TEXT_GENERATOR", "bedrock")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with pytest.raises(ConfigError, match="AWS_PROFILE"):
        get_config("development")
    monkeypatch.setenv("AWS_PROFILE", "default")
    with pytest.raises(ConfigError, match="AWS_PROFILE=default"):
        get_config("development")


def test_a_custom_model_id_can_be_configured(monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
    assert get_config("development").BEDROCK_MODEL_ID == "amazon.nova-pro-v1:0"


def test_the_timeout_defaults_to_ten_seconds(monkeypatch):
    monkeypatch.delenv("TEXT_GENERATION_TIMEOUT_SECONDS", raising=False)
    assert get_config("development").TEXT_GENERATION_TIMEOUT_SECONDS == 10


@pytest.mark.parametrize("value", ["0", "-3", "muchos"])
def test_the_timeout_must_be_a_positive_integer(monkeypatch, value):
    monkeypatch.setenv("TEXT_GENERATION_TIMEOUT_SECONDS", value)
    with pytest.raises(ConfigError, match="TEXT_GENERATION_TIMEOUT_SECONDS"):
        get_config("development")


def test_the_suite_never_talks_to_bedrock_whatever_the_env_says(monkeypatch):
    monkeypatch.setenv("TEXT_GENERATOR", "bedrock")
    config = get_config("test")
    assert config.TEXT_GENERATOR == "local"
    assert isinstance(build_text_generator(config), LocalTextGenerator)
