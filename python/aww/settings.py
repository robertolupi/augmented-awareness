import pathlib

from pydantic import BaseModel, DirectoryPath, field_validator
import textwrap
import platformdirs

from pydantic_settings import (
    BaseSettings,
    TomlConfigSettingsSource,
    PydanticBaseSettingsSource,
)

APP_NAME = "aww"
APP_AUTHOR = "rlupi"


def config_file():
    return (
        pathlib.Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR)) / "config.toml"
    )

# Overridden in tests and by CLI argument
CONFIG_FILE = config_file()

class ExpandedDirectoryPath(DirectoryPath):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        yield cls.expand_user

    @classmethod
    def expand_user(cls, value):
        return value.expanduser()


class ObsidianTips(BaseModel):
    model_name: str = "local"
    system_prompt: str = textwrap.dedent(
        """You're an helpful psychology, wellness and mindfulness coach.
        You answer with 5 helpful, short and actionable tips to live a more wholesome life.
        This was my schedule:
        """
    )
    user_prompt: str = "What can I do differently?"


class Obsidian(BaseModel):
    tips: ObsidianTips = ObsidianTips()
    vault: pathlib.Path

    @field_validator("vault", mode="before")
    def expand_path(cls, v):
        return pathlib.Path(v).expanduser()


class LlmModel(BaseModel):
    provider: str
    model: str


class LlmProvider(BaseModel):
    base_url: str


class Llm(BaseModel):
    model: dict[str, LlmModel]
    provider: dict[str, LlmProvider]


class Settings(BaseSettings):
    obsidian: Obsidian
    llm: Llm

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls, toml_file=CONFIG_FILE),)
