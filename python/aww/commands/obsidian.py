import datetime
import os
import subprocess

import click
import pyarrow as pa
import rich
import rich.columns
import rich.markdown
import rich.padding
import rich.table
from pydantic_ai.agent import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from aww import settings
from aww.observe.obsidian import Vault
from aww.orient.schedule import Schedule

vault: Vault
schedule: Schedule
config: settings.Settings


@click.group(name="obsidian")
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
def web():
    global vault
    os.environ["OBSIDIAN_VAULT"] = str(vault.path)
    subprocess.run(["streamlit", "run", "obsidian_web.py"])


def get_model(model_name: str) -> OpenAIModel:
    global config
    model_config = config.llm.model[model_name]
    provider_name = model_config.provider
    provider_config = config.llm.provider[provider_name]
    provider = OpenAIProvider(base_url=provider_config.base_url)
    return OpenAIModel(model_name=model_config.model, provider=provider)


@commands.command()
@click.option("model_name", "--model", "-m", default="local", help="LLM Model.")
@click.argument("user_prompt", type=str, required=False)
def tips(user_prompt: str | None = None, model_name: str | None = None):
    global config
    global schedule
    model_name = model_name or config.obsidian.tips.model_name
    system_prompt = config.obsidian.tips.system_prompt
    user_prompt = user_prompt or config.obsidian.tips.user_prompt

    model = get_model(model_name)
    agent = Agent(model=model, system_prompt=system_prompt)

    full_user_prompt = []
    for date, page in schedule.journal.items():
        full_user_prompt.append("")
        full_user_prompt.append("# " + date.strftime("On %A, %B %d:"))
        full_user_prompt.append(str(page.frontmatter()))
        for ev in page.events():
            full_user_prompt.append(" " + str(ev))
        full_user_prompt.append("")

    full_user_prompt.append("# Question")
    full_user_prompt.append(user_prompt)

    result = agent.run_sync("\n".join(full_user_prompt))
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
@click.option(
    "verbose", "-v", is_flag=True, help="Verbose output. Print markdown content."
)
@click.argument("page_name", type=str, required=False)
def info(verbose, page_name=None):
    """Print general information about a page."""
    global schedule
    journal = schedule.journal
    pages = journal.values()

    rich.print(f"Total Pages: {len(pages)}")
    rich.print(f"Journal pages: {len(journal)}")
    for entry in pages:
        rich.print(f"Page: {entry.name}")
        rich.print("Frontmatter:", entry.frontmatter())
        rich.print("Events:", rich.columns.Columns(entry.events()))
        rich.print("Tasks:", rich.columns.Columns(entry.tasks()))
        rich.print("Tags:", rich.columns.Columns(entry.tags()))
        if verbose:
            rich.print(rich.padding.Padding(entry.content(), 1))
            rich.print("\n")


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
