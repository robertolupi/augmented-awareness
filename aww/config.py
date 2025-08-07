from __future__ import annotations

from pathlib import Path
from typing import Dict, Literal, Union, Optional, Any

from pydantic import Field, BaseModel
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


class Settings(BaseSettings):
    models: Dict[str, ModelConfig] = Field(
        default_factory=lambda: {
            "openai": OpenAIConfig(),
            "gemini": GeminiConfig(),
            "local": LocalAIConfig(model_name="local-model"),
        }
    )
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
