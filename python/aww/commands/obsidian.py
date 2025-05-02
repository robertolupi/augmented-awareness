import re
from datetime import datetime, time
import os
import subprocess
from typing import List

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
    lines = page.content().splitlines()
    start, end = get_section(lines, context.settings.obsidian.journal_header_re)
    event_lines = [
        (n, m.group("time"), m.group("end_time"), m.group("name"))
        for n in range(start, end)
        if (m := EVENT_RE.match(lines[n]))
    ]
    # Modify last event: set end_time to time_, if it has no end_time
    if event_lines:
        if not event_lines[-1][2]:  # no end_time
            last_event = f"{event_lines[-1][1]} - {time_:%H:%M} {event_lines[-1][3]}"
            lines[event_lines[-1][0]] = last_event
    # Create a new open-ended event: set time to time_, and name to text
    new_event = f"{time_:%H:%M} {text}"
    lines.insert(end, new_event)
    # Rewrite the page file at page.path
    new_content = "\n".join(lines)
    with open(page.path, "w") as f:
        f.write(new_content)


def get_section(lines: List[str], header: str):
    header_re = re.compile("^(#+)\\s+" + header + "$")
    section_start = None
    if not lines:
        raise ValueError("page content is empty")
    for n, line in enumerate(lines):
        if m := header_re.match(line):
            section_start = m.group(1) + " "
            break
    section = None
    for k in range(n + 1, len(lines)):
        if lines[k].startswith(section_start):
            section = (n + 1, k)
            break
    if not section:
        section = (n + 1, len(lines))
    return section
