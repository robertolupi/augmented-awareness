import enum
import os
from pathlib import Path

import click

from aww import config
from aww.config import OpenAIConfig, GeminiConfig, LocalAIConfig
from aww.obsidian import Vault
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


class NoCachePolicyChoice(enum.Enum):
    CACHE = "do_cache"
    ROOT = "root"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    MTIME = "mtime"
    ONE_HOUR = "1h"


settings = config.Settings()


def create_model(model_name: str) -> Model:
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


@click.group()
@click.option("-m", "--model", "model_name", type=str, default=settings.default_model)
@click.option("--vault-path", type=click.Path(), default=settings.vault_path)
@click.option("--journal-dir", type=str, default=settings.journal_dir)
@click.option("--retrospectives-dir", type=str, default=settings.retrospectives_dir)
@click.pass_context
def main(
    ctx,
    model_name,
    vault_path,
    journal_dir,
    retrospectives_dir,
):
    llm_model = create_model(model_name)
    vault_path = os.path.expanduser(vault_path)
    vault = Vault(Path(vault_path), journal_dir, retrospectives_dir)
    ctx.obj = {
        "llm_model": llm_model,
        "vault": vault,
        "settings": settings,
        "model_name": model_name,
    }
