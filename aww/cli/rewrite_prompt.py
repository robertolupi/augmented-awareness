import asyncio
import datetime
import textwrap
from pathlib import Path

import click
import rich
from pydantic_ai import Agent
from rich.markdown import Markdown

import aww
import aww.retro
import aww.retro_gen
from aww import retro
from aww.cli import main
from aww.config import create_model
from aww.obsidian import Level
import aww.prompt_engineering


@main.command()
@click.option("--critique-model", type=str, default="local")
@click.option(
    "-d", "--date", type=click.DateTime(), default=datetime.date.today().isoformat()
)
@click.option(
    "-c",
    "--context",
    type=click.Choice(Level, case_sensitive=False),
    multiple=True,
    help="Context levels for retrospective",
    default=[Level.daily, Level.weekly, Level.monthly, Level.yearly],
)
@click.argument("level", type=click.Choice(Level, case_sensitive=False))
@click.option(
    "-y",
    "--yesterday",
    is_flag=True,
    default=False,
    help="Switch to previous date (only for daily level)",
)
@click.pass_context
def rewrite_prompt(
    ctx,
    critique_model: str,
    date,
    yesterday,
    context,
    level,
):
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    if yesterday:
        date = date - datetime.timedelta(days=1)

    prompt_file = Path(aww.__file__).parent / "prompts" / f"{level.value}.md"
    prompt = prompt_file.read_text()

    # Convert datetime to date
    query_date = date.date() if isinstance(date, datetime.datetime) else date

    result = aww.prompt_engineering.rewrite_prompt_logic(
        critique_model_name=critique_model,
        llm_model=llm_model,
        vault=vault,
        date=query_date,
        level=level,
        context_levels=list(context),
        current_prompt=prompt,
    )

    rich.print(Markdown(result))
    prompt_file.write_text(result)
