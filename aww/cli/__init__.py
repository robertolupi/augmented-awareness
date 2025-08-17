import enum
import os
from pathlib import Path

import click

from aww import config
from aww.config import create_model
from aww.obsidian import Vault


class NoCachePolicyChoice(enum.Enum):
    CACHE = "do_cache"
    ROOT = "root"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    MTIME = "mtime"
    ONE_HOUR = "1h"


@click.group()
@click.pass_context
def main(
    ctx,
):
    settings = config.Settings()
    llm_model = create_model(settings.default_model)
    vault = Vault.from_settings(settings)
    ctx.obj = {
        "llm_model": llm_model,
        "vault": vault,
        "settings": settings,
        "model_name": settings.default_model,
    }
