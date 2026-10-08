import os

import app.config as config_module
from app.config import get_config, load_env_file


def _write_env(tmp_path, monkeypatch, body):
    env_file = tmp_path / ".env"
    env_file.write_text(body, encoding="utf-8")
    monkeypatch.setattr(config_module, "ENV_FILE", env_file)


def test_development_reads_values_from_env_file(tmp_path, monkeypatch):
    _write_env(tmp_path, monkeypatch, "CORS_ALLOWED_ORIGINS=https://from-dotenv.example\n")
    # set-then-delete so monkeypatch undoes the variable even though load_dotenv writes it
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "placeholder")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS")

    load_env_file("development")

    assert get_config("development").CORS_ALLOWED_ORIGINS == ["https://from-dotenv.example"]


def test_real_environment_variables_win_over_env_file(tmp_path, monkeypatch):
    _write_env(tmp_path, monkeypatch, "CORS_ALLOWED_ORIGINS=https://from-dotenv.example\n")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://from-environment.example")

    load_env_file("development")

    assert get_config("development").CORS_ALLOWED_ORIGINS == ["https://from-environment.example"]


def test_production_never_reads_env_file(tmp_path, monkeypatch):
    _write_env(tmp_path, monkeypatch, "CORS_ALLOWED_ORIGINS=https://from-dotenv.example\n")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "placeholder")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS")

    load_env_file("production")

    assert "CORS_ALLOWED_ORIGINS" not in os.environ
