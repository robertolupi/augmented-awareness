import enum
import os

import click
from pathlib import Path

from aww import config
from aww.obsidian import Vault
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


class Provider(enum.Enum):
    LOCAL = "local"
    GEMINI = "gemini"
    OPENAI = "openai"


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


@click.group()
@click.option("--local_model", type=str, default=settings.local_model)
@click.option("--local_url", type=str, default=settings.local_base_url)
@click.option("--gemini_model", type=str, default=settings.gemini_model)
@click.option("--openai_model", type=str, default=settings.openai_model)
@click.option(
    "-p",
    "--provider",
    type=click.Choice(Provider, case_sensitive=False),
    default="local",
)
@click.option("--vault_path", type=click.Path(), default=settings.vault_path)
@click.option("--journal_dir", type=str, default=settings.journal_dir)
@click.option("--retrospectives_dir", type=str, default=settings.retrospectives_dir)
@click.pass_context
def main(
    ctx,
    provider,
    local_model,
    local_url,
    gemini_model,
    openai_model,
    vault_path,
    journal_dir,
    retrospectives_dir,
):
    llm_model = make_model(gemini_model, local_model, local_url, openai_model, provider)
    vault_path = os.path.expanduser(vault_path)
    vault = Vault(Path(vault_path), journal_dir, retrospectives_dir)
    ctx.obj = {
        "llm_model": llm_model,
        "vault": vault,
        "settings": settings,
    }


def make_model(gemini_model, local_model, local_url, openai_model, provider):
    match provider:
        case Provider.LOCAL:
            model = OpenAIModel(
                model_name=local_model, provider=OpenAIProvider(base_url=local_url)
            )
        case Provider.GEMINI:
            if "GEMINI_API_KEY" not in os.environ:
                raise click.ClickException(
                    "Please set environment variable GEMINI_API_KEY"
                )
            model = GeminiModel(model_name=gemini_model)
        case Provider.OPENAI:
            if "OPENAI_API_KEY" not in os.environ:
                raise click.ClickException(
                    "Please set environment variable OPENAI_API_KEY"
                )
            model = OpenAIModel(model_name=openai_model)
        case _:
            raise click.ClickException(f"Unknown provider: {provider}")
    return model
