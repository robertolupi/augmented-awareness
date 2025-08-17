import click
import rich

import os

from aww.cli import main


@main.command()
@click.pass_context
def show_config(ctx):
    """Show AWW configuration settings."""
    rich.print(ctx.obj["settings"])
