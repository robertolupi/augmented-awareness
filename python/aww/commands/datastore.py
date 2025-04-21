import sys

import click
import rich
import rich.prompt
from sqlmodel import create_engine, SQLModel

from aww import context

import aww.datastore.models  # noqa: F401


@click.group(name="datastore")
def commands():
    """Manage the datastore."""
    pass


@commands.command()
def init():
    """Initialize the datastore."""
    settings = context.settings
    if settings.sqlite_db.exists():
        rich.print(f"[red]Database already exists at {settings.sqlite_db}[/red]")
        ok = rich.prompt.Confirm.ask("Do you want to overwrite it?", default=False)
        if not ok:
            sys.exit(1)
            return
        settings.sqlite_db.unlink()
    settings.sqlite_db.parent.mkdir(parents=True, exist_ok=True)
    rich.print(f"Creating database at {settings.sqlite_db}")
    engine = create_engine(settings.sqlite_url)
    SQLModel.metadata.create_all(engine)
    rich.print(f"Database created at [green]{settings.sqlite_db}[/green]")
    if not settings.data_path.exists():
        rich.print(f"Creating data directory at [green]{settings.data_path}[/green]")
        settings.data_path.mkdir(parents=True, exist_ok=True)
    else:
        rich.print(
            f"Data directory already exists at [yellow]{settings.data_path}[/yellow]"
        )
