import os
import pathlib
import subprocess
import sys

import click
import rich
import tomlkit

path: pathlib.Path
configuration: tomlkit.TOMLDocument = tomlkit.document()


@click.group(name="config")
def commands():
    """Show or edit the configuration file."""
    pass


@commands.command()
def edit():
    editor = os.environ.get("EDITOR")
    if not editor:
        rich.print("[red]no EDITOR in environment[/red]")
        sys.exit(1)
    subprocess.run([editor, path])


@commands.command()
def show():
    global path, configuration
    rich.print(f"[b]Config file:[/b] {str(path)!r}")
    rich.print(configuration)
