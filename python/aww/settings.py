import pathlib

from pydantic import BaseModel, DirectoryPath, field_validator
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


class Obsidian(BaseModel):
    vault: pathlib.Path = "~/Documents/Obsidian Vault"
    journal_header_re: str = "Journal and events"

    @field_validator("vault", mode="before")
    def expand_path(cls, v):
        return pathlib.Path(v).expanduser()


class LlmModel(BaseModel):
    provider: str
    model: str


class LlmProvider(BaseModel):
    base_url: str | None = None
    api_key: str | None = None


class LlmAgent(BaseModel):
    model_name: str = "local"
    system_prompt: str = ""
    user_prompt: str = ""
    settings: dict | None = None


class Llm(BaseModel):
    model: dict[str, LlmModel]
    provider: dict[str, LlmProvider]
    agent: dict[str, LlmAgent]


class ActivityWatch(BaseModel):
    client_name: str = "aww"


class Settings(BaseSettings):
    obsidian: Obsidian
    llm: Llm
    activitywatch: ActivityWatch = ActivityWatch()

    sqlite_db: pathlib.Path = (
        pathlib.Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR)) / "aww.db"
    )
    data_path: pathlib.Path = (
        pathlib.Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR)) / "data"
    )

    @property
    def sqlite_url(self) -> str:
        return "sqlite:///" + str(self.sqlite_db)

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
