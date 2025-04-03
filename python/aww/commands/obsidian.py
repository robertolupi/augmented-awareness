import collections
import datetime

import click
import rich
import rich.columns
import rich.table
import rich.markdown
import os
import subprocess

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.agent import Agent

from aww import settings
from aww.observe.obsidian import Vault

vault: Vault
config : settings.Settings

@click.group(name="obsidian")
@click.option(
    "vault_path",
    "--vault",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
def commands(vault_path=None):
    """Observe the content of an Obsidian vault."""
    global vault
    global config
    config = settings.Settings()
    vault = Vault(config.obsidian.vault)


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
def tips(model_name: str | None = None):
    global config
    model_name = model_name or config.obsidian.tips.model_name
    system_prompt = config.obsidian.tips.system_prompt
    user_prompt = config.obsidian.tips.user_prompt

    model = get_model(model_name)
    agent = Agent(model=model, system_prompt=system_prompt)

    global vault
    date_end = datetime.date.today()
    date_start = date_end - datetime.timedelta(days=7)
    journal = vault.journal()

    date = date_start
    full_user_prompt = []
    while date <= date_end:
        if date in journal:
            page = journal[date]
            full_user_prompt.append("")
            full_user_prompt.append("# " + date.strftime("On %A, %B %d:"))
            for ev in page.events():
                full_user_prompt.append(" " + str(ev))
            full_user_prompt.append("")
        date = date + datetime.timedelta(days=1)

    full_user_prompt.append("# Question")
    full_user_prompt.append(user_prompt)

    result = agent.run_sync("\n".join(full_user_prompt))
    md = rich.markdown.Markdown(result.data)
    rich.print(md)


@commands.command()
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


@commands.command()
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
