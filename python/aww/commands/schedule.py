import datetime
from typing import List

import click
import pyarrow as pa
import rich
import rich.markdown
import rich.table

from aww import settings
from aww.llm import get_agent
from aww.observe.obsidian import Vault, Event, Task
from aww.orient.schedule import Schedule

vault: Vault
schedule: Schedule
config: settings.Settings


@click.group(name="schedule")
@click.option(
    "vault_path",
    "--vault",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
@click.option(
    "date_start",
    "--date-start",
    "-s",
    type=click.DateTime(),
    default=(datetime.date.today() - datetime.timedelta(days=8)).strftime("%Y-%m-%d"),
)
@click.option(
    "date_end",
    "--date-end",
    "-e",
    type=click.DateTime(),
    default=(datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
)
@click.option(
    "date",
    "--date",
    "-d",
    help="Specify a single date (overrides date_start and date_end)",
    type=click.DateTime(),
    default=None,
)
@click.option("today", "-t", "--today", is_flag=True, help="Set dates to today.")
def commands(
    date_start: datetime.date | datetime.datetime,
    date_end: datetime.date | datetime.datetime,
    date: datetime.date | datetime.datetime,
    today: bool = False,
    vault_path=None,
):
    """Observe the content of an Obsidian vault."""
    global vault
    global schedule
    global config
    config = settings.Settings()
    vault = Vault(vault_path or config.obsidian.vault)
    date_start = date_start.date()
    date_end = date_end.date()
    if date:
        date_start = date.date()
        date_end = date.date()
    elif today:
        date_start = datetime.date.today()
        date_end = datetime.date.today()
    schedule = Schedule(vault.journal().subrange(date_start, date_end))


@commands.command()
@click.option("agent_name", "--agent", "-a", default="tips", help="LLM Agent config.")
@click.option("model_name", "--model", "-m", default=None, help="LLM Model.")
@click.argument("user_prompt", type=str, required=False)
def ask(
    user_prompt: str | None,
    model_name: str | None,
    agent_name: str | None,
):
    global schedule
    agent, default_user_prompt = get_agent(agent_name, model_name)

    @agent.tool_plain
    def read_schedule() -> List[Event]:
        """Read the user schedule."""
        return [event for page in schedule.journal.values() for event in page.events()]

    @agent.tool_plain
    def read_tasks() -> List[Task]:
        """Read the user tasks."""
        return [task for page in schedule.journal.values() for task in page.tasks()]

    result = agent.run_sync(user_prompt or default_user_prompt)
    md = rich.markdown.Markdown(result.data)
    rich.print(md)


@commands.command()
@click.option(
    "verbose", "-v", is_flag=True, help="Verbose output. Print dates and events."
)
def busy(verbose: bool = False):
    """Print schedule information for a date range.

    Obtains the events, then compute the time spent between each event and the next, compute sums by tags.
    """
    global schedule

    if verbose:
        for date, page in schedule.journal.items():
            events = page.events()
            if events:
                rich.print(f"[b]{date}[/]")
                for ev in events:
                    rich.print(f"  {ev.time} ({ev.duration}) {ev.name} {ev.tags}")

    t = rich.table.Table()
    t.add_column("Tag", justify="left", style="cyan", no_wrap=True)
    t.add_column("Total", justify="right", style="magenta")
    t.add_column("Histogram", justify="right", style="green", no_wrap=True)
    for row in schedule.total_duration_by_tag().to_pylist():
        t.add_row(
            row["tag"],
            str(row["duration"]),
            generate_sparkline(row["histogram"]),
        )
    rich.print(t)


def print_table(table: pa.Table):
    """Print a pyarrow table as a rich table."""
    t = rich.table.Table()
    for col in table.column_names:
        t.add_column(col)
    for row in table.to_pylist():
        t.add_row(*(str(row[col]) for col in table.column_names))
    rich.print(t)


@commands.command()
def tasks():
    global schedule
    for page in schedule.journal.values():
        tasks = page.tasks()
        if tasks:
            rich.print(page.name)
            for t in tasks:
                rich.print("  ", t)


def generate_sparkline(numbers: list[int]) -> rich.text.Text:
    """Generate a sparkline from a list of numbers using Unicode block characters.

    Args:
        numbers: List of integers to visualize

    Returns:
        A Rich Text object containing the sparkline
    """
    if not numbers:
        return ""

    min_val = min(numbers)
    max_val = max(numbers)

    # Normalize values to 0-7 range for block characters
    normalized = []
    if max_val != min_val:
        normalized = [int(7 * (x - min_val) / (max_val - min_val)) for x in numbers]
    else:
        normalized = [0 for _ in numbers]

    # Unicode block characters from lower to higher
    blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    spark_text = ""
    for level in normalized:
        spark_text += blocks[level]

    return spark_text
