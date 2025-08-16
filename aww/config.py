from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Literal, Union, Optional, Any

import click
from pydantic import Field, BaseModel
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)


class OpenAIConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    model_name: str = "gpt-4.1"
    model_settings: Dict[str, Any] = Field(default_factory=dict)


class GeminiConfig(BaseModel):
    provider: Literal["gemini"] = "gemini"
    model_name: str = "gemini-2.5-flash"
    model_settings: Dict[str, Any] = Field(default_factory=dict)


class LocalAIConfig(BaseModel):
    provider: Literal["local"] = "local"
    model_name: str
    base_url: str = "http://localhost:1234/v1"
    model_settings: Dict[str, Any] = Field(default_factory=dict)


ModelConfig = Union[OpenAIConfig, GeminiConfig, LocalAIConfig]


class RagConfig(BaseModel):
    provider: str = "sentence-transformers"
    model_name: str = "all-mpnet-base-v2"


class Settings(BaseSettings):
    models: Dict[str, ModelConfig] = Field(
        default_factory=lambda: {
            "openai": OpenAIConfig(),
            "gemini": GeminiConfig(),
            "local": LocalAIConfig(model_name="local-model"),
        }
    )
    rag: RagConfig = Field(default_factory=RagConfig)
    default_model: str = "local"

    vault_path: str = "~/data/notes"
    data_path: str = "~/data/aww"
    journal_dir: str = "journal"
    retrospectives_dir: str = "retrospectives"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            TomlConfigSettingsSource(settings_cls, Path("aww.toml")),
            # TomlConfigSettingsSource(settings_cls, Path("~/.aww.toml").expanduser()),
            env_settings,
            dotenv_settings,
            init_settings,
        )


def create_model(model_name: str) -> Model:
    settings = Settings()
    if model_name not in settings.models:
        raise click.ClickException(f"Model '{model_name}' not found in settings.")

    model_config = settings.models[model_name]

    if isinstance(model_config, OpenAIConfig):
        if not os.environ.get("OPENAI_API_KEY"):
            raise click.ClickException(
                "Please set environment variable OPENAI_API_KEY or api_key in config."
            )
        return OpenAIModel(
            model_name=model_config.model_name,
            **model_config.model_settings,
        )
    elif isinstance(model_config, GeminiConfig):
        if not os.environ.get("GEMINI_API_KEY"):
            raise click.ClickException(
                "Please set environment variable GEMINI_API_KEY or api_key in config."
            )
        return GeminiModel(
            model_name=model_config.model_name,
            **model_config.model_settings,
        )
    elif isinstance(model_config, LocalAIConfig):
        return OpenAIModel(
            model_name=model_config.model_name,
            provider=OpenAIProvider(base_url=model_config.base_url),
            **model_config.model_settings,
        )
    else:
        # This should not be reached if config parsing is correct
        raise click.ClickException(
            f"Unknown provider for model '{model_name}' with config {model_config}"
        )
