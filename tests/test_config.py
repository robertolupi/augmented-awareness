from unittest.mock import patch

import click
import pytest

from aww.config import OpenRouterConfig, Settings, create_model


def test_create_model_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    settings = Settings(
        models={"router": OpenRouterConfig(model_name="openai/gpt-4.1-mini")}
    )
    with patch("aww.config.Settings", return_value=settings):
        model = create_model("router")
    assert model.model_name == "openai/gpt-4.1-mini"


def test_create_model_openrouter_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    settings = Settings(models={"router": OpenRouterConfig()})
    with patch("aww.config.Settings", return_value=settings):
        with pytest.raises(click.ClickException, match="OPENROUTER_API_KEY"):
            create_model("router")


def test_model_name_env_override(monkeypatch):
    monkeypatch.setenv("AWW_MODELS__OPENROUTER__PROVIDER", "openrouter")
    monkeypatch.setenv("AWW_MODELS__OPENROUTER__MODEL_NAME", "deepseek/deepseek-v3")
    settings = Settings()
    openrouter = settings.models["openrouter"]
    assert isinstance(openrouter, OpenRouterConfig)
    assert openrouter.model_name == "deepseek/deepseek-v3"


def test_ignored_journal_headers_default(monkeypatch, tmp_path):
    monkeypatch.setenv("AWW_CONFIG_FILE", str(tmp_path / "missing.toml"))
    settings = Settings()
    assert settings.ignored_journal_headers == []


def test_ignored_journal_headers_env_override(monkeypatch):
    monkeypatch.setenv("AWW_IGNORED_JOURNAL_HEADERS", '["Gratitude", "Mood Tracker"]')
    settings = Settings()
    assert settings.ignored_journal_headers == ["Gratitude", "Mood Tracker"]
