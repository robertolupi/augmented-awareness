from datetime import datetime, time
import os
import subprocess

import click
import rich
import rich.columns
import rich.padding

from aww import settings
from aww import context
from aww.observe.obsidian import Vault
from aww.observe.obsidian.events import EVENT_RE

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


@commands.command()
@click.option(
    "date_",
    "-d",
    "--date",
    type=click.DateTime(),
    required=True,
    default=datetime.now(),
)
@click.option("time_", "-t", "--time", type=str, required=False)
@click.argument("text", type=str, required=True)
def record(date_: datetime, text: str, time_: str | None = None):
    """Record a new event."""
    # Events are stored in the journal pages by date, in a specific section identified by a regex in settings
    # The section containing events may contain other text, which shall be preserved.
    # Events are lines like "HH:MM text" or "HH:MM - HH:MM text"
    page = context.journal.get(date_.date())
    if not page:
        rich.print("[red]Page {date.date()} not found[/red]")
        return
    if time_:
        time_ = time.fromisoformat(time_)
    else:
        time_ = datetime.now().time()

    section = page.get_section(context.settings.obsidian.journal_header_re)
    events = [
        (n, m) for n, line in enumerate(section.lines) if (m := EVENT_RE.match(line))
    ]
    if events:
        if not events[-1][1].group("end_time"):
            last_event = f"{events[-1][1].group('time')} - {time_:%H:%M} {events[-1][1].group('name')}\n"
            section.lines[events[-1][0]] = last_event
    # Create a new open-ended event: set time to time_, and name to text
    new_event = f"{time_:%H:%M} {text}\n"
    section.lines.append(new_event)
    # Rewrite the page file at page.path
    section.save()
