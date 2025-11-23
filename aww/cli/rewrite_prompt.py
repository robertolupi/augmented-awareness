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
@click.argument("level", type=str)
@click.option(
    "-y",
    "--yesterday",
    is_flag=True,
    default=False,
    help="Switch to previous date (only for daily level)",
)
@click.option(
    "-f",
    "--feedback",
    multiple=True,
    help="Feedback comments for optimization (used for MOTD).",
)
@click.pass_context
def rewrite_prompt(
    ctx,
    critique_model: str,
    date,
    yesterday,
    context,
    level,
    feedback,
):
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    if yesterday:
        date = date - datetime.timedelta(days=1)

    # Convert datetime to date
    query_date = date.date() if isinstance(date, datetime.datetime) else date

    if level.lower() == "motd":
        from aww.cli.motd import get_motd_context

        prompt_file = Path(aww.__file__).parent / "prompts" / "motd.md"
        prompt = prompt_file.read_text()

        # Gather context for MOTD (using defaults for now, could expose options)
        test_inputs = get_motd_context(vault)

        feedback_list = [{"comment": f, "context": "CLI Feedback"} for f in feedback]

        result = aww.prompt_engineering.optimize_prompt(
            critique_model_name=critique_model,
            llm_model=llm_model,
            current_prompt=prompt,
            test_inputs=test_inputs,
            feedback=feedback_list,
        )
    else:
        try:
            level_enum = Level(level)
        except ValueError:
            raise click.BadParameter(
                f"Invalid level: {level}. Must be one of {[l.value for l in Level]} or 'motd'."
            )

        prompt_file = Path(aww.__file__).parent / "prompts" / f"{level_enum.value}.md"
        prompt = prompt_file.read_text()

        result = aww.prompt_engineering.rewrite_prompt_logic(
            critique_model_name=critique_model,
            llm_model=llm_model,
            vault=vault,
            date=query_date,
            level=level_enum,
            context_levels=list(context),
            current_prompt=prompt,
            external_feedback=list(feedback),
        )

    rich.print(Markdown(result))
    prompt_file.write_text(result)
