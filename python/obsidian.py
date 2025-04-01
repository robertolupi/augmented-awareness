import collections
import datetime
import click
import rich
import rich.columns
import rich.table
import os
import subprocess

from aww.observe.obsidian import Vault

vault: Vault


@click.group()
@click.argument(
    "vault_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
def main(vault_path):
    """Observe the content of an Obsidian vault."""
    global vault
    vault = Vault(vault_path)


@main.command()
def web():
    global vault
    os.environ["OBSIDIAN_VAULT"] = str(vault.path)
    subprocess.run(["streamlit", "run", "obsidian_web.py"])


@main.command()
@click.option(
    "date_start",
    "-s",
    type=click.DateTime(),
    default=(datetime.date.today() - datetime.timedelta(days=8)).strftime("%Y-%m-%d"),
)
@click.option(
    "date_end",
    "-e",
    type=click.DateTime(),
    default=(datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
)
@click.option("today", "-t", "--today", is_flag=True, help="Set dates to today.")
@click.option(
    "verbose", "-v", is_flag=True, help="Verbose output. Print dates and events."
)
def busy(
    date_start: datetime.date | datetime.datetime,
    date_end: datetime.date | datetime.datetime,
    verbose: bool = False,
    today: bool = False,
):
    """Print schedule information for a date range.

    Obtains the events, then compute the time spent between each event and the next, compute sums by tags.
    """
    global vault
    journal = vault.journal()
    date_start = date_start.date()
    date_end = date_end.date()
    if today:
        date_start = datetime.date.today()
        date_end = datetime.date.today()
    date = date_start
    tag_durations = collections.defaultdict(lambda: datetime.timedelta())
    while date <= date_end:
        if verbose:
            rich.print(date)
        if date in journal:
            page = journal[date]
            events = page.events()
            for ev in events:
                if ev.duration is not None:
                    for tag in ev.tags:
                        tag_durations[tag] += ev.duration
                if verbose:
                    rich.print(
                        f"  [bold]{ev.time}[/] {ev.name} {ev.tags} ({ev.duration})"
                    )
        date = date + datetime.timedelta(days=1)

    durations = list(tag_durations.items())
    durations.sort(key=lambda x: x[1], reverse=True)

    table = rich.table.Table()
    table.add_column("tag")
    table.add_column("duration")
    for tag, duration in durations:
        table.add_row(tag, str(duration))
    rich.print(table)


@main.command()
@click.option(
    "verbose", "-v", is_flag=True, help="Verbose output. Print markdown content."
)
@click.argument("page_name", type=str, required=False)
def info(verbose, page_name=None):
    """Print general information about a page."""
    global vault
    rich.print(vault.path)
    pages = vault.pages()
    journal = vault.journal()

    rich.print(f"Total Pages: {len(pages)}")
    rich.print(f"Journal pages: {len(journal)}")
    if not page_name:
        entry = list(journal.values())[-1]
    else:
        entry = pages.get(page_name)
    if not entry:
        rich.print("[bold red]Page not found[/bold red]")
        return
    rich.print("\n")
    rich.print(f"Page: {entry.name}")
    rich.print("Frontmatter:", entry.frontmatter())
    rich.print("Events:", rich.columns.Columns(entry.events()))
    rich.print("Tasks:", rich.columns.Columns(entry.tasks()))
    rich.print("Tags:", rich.columns.Columns(entry.tags()))
    if verbose:
        rich.print(entry.content())


if __name__ == "__main__":
    main()
