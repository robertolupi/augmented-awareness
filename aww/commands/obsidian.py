import os
import subprocess

import click
import rich
import rich.columns
import rich.padding

from aww import settings
from aww import context
from aww.observe.obsidian import Vault

vault: Vault
config: settings.Settings


@click.group(name="obsidian")
@click.option(
    "vault_path",
    "--vault",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
def commands(
    vault_path=None,
):
    """Observe the content of an Obsidian vault."""
    if vault_path:
        context.vault = Vault(vault_path)


@commands.command()
def web():
    os.environ["OBSIDIAN_VAULT"] = str(context.vault.path)
    subprocess.run(["streamlit", "run", "obsidian_web.py"])


@commands.command()
@click.option(
    "verbose", "-v", is_flag=True, help="Verbose output. Print markdown content."
)
@click.argument("page_name", type=str, required=False)
def info(verbose, page_name):
    """Print general information about a page."""
    page = context.vault.pages()[page_name]
    rich.print(f"Page: {page.name}")
    rich.print("Frontmatter:", page.frontmatter())
    rich.print("Events:", rich.columns.Columns(page.events()))
    rich.print("Tasks:", rich.columns.Columns(page.tasks()))
    rich.print("Tags:", rich.columns.Columns(page.tags()))
    if verbose:
        rich.print(rich.padding.Padding(page.content(), 1))
        rich.print("\n")
