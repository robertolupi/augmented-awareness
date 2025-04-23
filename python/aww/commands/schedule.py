from dataclasses import dataclass
import datetime
import textwrap
from typing import List

import click
import pyarrow as pa
import rich
import rich.markdown
import rich.table

from pydantic_ai import Agent

from aww import context
from aww.llm import get_agent, get_model
from aww.observe.obsidian import Event, Task
from aww.orient.schedule import Schedule


schedule: Schedule


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
    global schedule
    date_start = date_start.date()
    date_end = date_end.date()
    if date:
        date_start = date.date()
        date_end = date.date()
    elif today:
        date_start = datetime.date.today()
        date_end = datetime.date.today()
    schedule = Schedule(context.vault.journal().subrange(date_start, date_end))


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


def read_schedule() -> List[Event]:
    """Read the user schedule."""
    global schedule
    rich.print("[blue]Agent called read_schedule[/blue]")
    return [event for page in schedule.journal.values() for event in page.events()]


def read_tasks() -> List[Task]:
    """Read the user tasks."""
    global schedule
    rich.print("[blue]Agent called read_tasks[/blue]")
    return [task for page in schedule.journal.values() for task in page.tasks()]


def get_current_date() -> str:
    """Returns the current date."""
    rich.print("[blue]Agent called get_current_date[/blue]")
    return f"The current date is {datetime.date.today()}"


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

    @agent.system_prompt
    def system_prompt():
        return "You are a helpful assistant skilled in psychology and coaching. You can read the user schedule and tasks."

    agent.tool_plain(read_schedule)
    agent.tool_plain(read_tasks)

    result = agent.run_sync(user_prompt or default_user_prompt)
    md = rich.markdown.Markdown(result.data)
    rich.print(md)


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


@dataclass
class Concept:
    concept_id: str
    parent_concept_id: str
    description: str


@commands.command()
@click.option("model_name", "--model", "-m", default="local")
def concepts(model_name: str):
    """Extract concepts from schedule or tasks."""
    global schedule
    model = get_model(model_name)
    agent = Agent(
        model=model,
        result_type=List[Concept],
        system_prompt=textwrap.dedent(
            """Extract concepts from the user schedule.
            Concepts refer to the user physical, mental and emotional state, and the corresponding activities that generated them.
            Concepts correspond to activities and can be hierarchically organized. Make sure to include a description of the activity in a complete phrase.
            Concepts are generic and do not include specific details (e.g. "waking up early" is a good concept, "waking up at 4:05 AM" is a bad concept because it is too specific).
            Hashtags always refer to concepts, an hashtag such as #consume/read/web refers to three concepts in a hierarchy: content consumption, reading, reading on the web. "reading on the web" has "reading" as parent concept, "reading" has "content consumption" as parent concept
            The parent_concept_id refers to the name of the parent concept.
            
            Think step by step, first draft a list of concepts, then identify the hierarchical connections. If two concepts are very close, introduce a new parent concept. Remember that concepts refer to the user's states (physical, mental, and emotional) and activities.
                      """
        ),
    )
    agent.tool_plain(read_schedule)
    agent.tool_plain(read_tasks)
    agent.tool_plain(get_current_date)
    result = agent.run_sync(
        user_prompt="Extract concepts from the user schedule and tasks, and return them as JSON."
    )
    rich.print(result)
