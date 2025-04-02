import os
import pathlib
import subprocess
import sys

import click
import rich
import rich.prompt
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


@commands.command(name='path')
def print_path():
    """Print the path to the configuration file."""
    print(path)


@commands.command()
def init():
    # path = pathlib.Path('.')
    global path
    path.parent.mkdir(parents=True, exist_ok=True)
    rich.print(path)
    if path.exists():
        choice = rich.prompt.Confirm.ask(f"Overwrite {path}?")
        if not choice:
            return
    from tomlkit import document, table

    obsidian = table()
    obsidian.add("vault", "~/data/notes")

    tips = table()
    tips.add("model_name", "local")
    tips.add(
        "system_prompt",
        "You're an helpful psychology, wellness and mindfulness coach.\nYou answer with 5 helpful, short and actionable tips to live a more wholesome life.\nThis was my schedule:\n",
    )
    tips.add("user_prompt", "What can I do differently?")
    obsidian.add("tips", tips)

    llm = table()
    provider = table()
    provider_local = table()
    provider_local.add("base_url", "http://localhost:1234/v1/")
    provider.add("local", provider_local)
    llm.add("provider", provider)

    model = table()
    model_local = table()
    model_local.add("provider", "local")
    model_local.add("model", "gemma-3-4b-it")
    model.add("local", model_local)
    llm.add("model", model)

    doc = document()
    doc.add("obsidian", obsidian)
    doc.add("llm", llm)
    path.write_text(tomlkit.dumps(doc))
