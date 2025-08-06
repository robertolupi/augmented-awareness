from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)

from pydantic_ai.models.openai import OpenAIModelName as OpenAIModel
from pydantic_ai.models.google import GoogleModelName as GoogleAIModel


class Settings(BaseSettings):
    openai_model: OpenAIModel = "gpt-4.1"
    gemini_model: GoogleAIModel = "gemini-2.5-flash"
    local_model: str = ""
    local_base_url: str = "http://localhost:1234/v1"

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
            TomlConfigSettingsSource(settings_cls, Path("~/.aww.toml").expanduser()),
            env_settings,
            dotenv_settings,
            init_settings,
        )
