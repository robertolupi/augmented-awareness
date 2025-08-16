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


settings = config.Settings()


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
