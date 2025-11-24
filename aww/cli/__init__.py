import click

from aww import config
from aww.config import create_model
from aww.obsidian import Vault


@click.group()
@click.pass_context
def main(
    ctx,
):
    settings = config.Settings()
    llm_model = create_model(settings.model)
    vault = Vault.from_settings(settings)
    ctx.obj = {
        "llm_model": llm_model,
        "vault": vault,
        "settings": settings,
        "model_name": settings.model,
    }
