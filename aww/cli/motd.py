import datetime
from pathlib import Path

import click

import rich
from rich.markdown import Markdown
import aww
from aww.cli import main

from pydantic_ai import Agent

from aww.obsidian import Level
from aww.prompts import get_prompt_template


@main.command()
@click.option("--output-file", type=click.Path(), help="File to write the output to.")
@click.option("-d", "--daily", is_flag=True, help="Include daily note.")
@click.option(
    "-y", "--yesterday", is_flag=True, help="Include yesterday retrospective."
)
@click.option("-w", "--weekly", is_flag=True, help="Include weekly retrospective.")
@click.option(
    "--plain-text",
    is_flag=True,
    default=False,
    help="Output plain text instead of markdown.",
)
@click.pass_context
def motd(ctx, output_file, plain_text, daily, yesterday, weekly):
    """Show a motivational message of the day."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]

    prompt = get_prompt_template("motd.md").render()

    agent = Agent(model=llm_model, system_prompt=prompt)

    user_prompt = []

    if daily:
        daily_notes = vault.page(datetime.date.today(), Level.daily)
        if daily_notes:
            user_prompt += daily_notes.content()
    if yesterday:
        yesterday_retro = vault.retrospective_page(
            datetime.date.today() - datetime.timedelta(days=1), Level.daily
        )
        if yesterday_retro:
            user_prompt += yesterday_retro.content()
    if weekly:
        weekly_retro = vault.retrospective_page(datetime.date.today(), Level.weekly)
        if weekly_retro:
            user_prompt += weekly_retro.content()

    user_prompt += f'Now, it is {datetime.datetime.now().strftime("%m/%d/%Y %H:%M")}'

    response = agent.run_sync(user_prompt)
    if plain_text:
        print(response.output)
    else:
        rich.print(Markdown(response.output))

    if output_file:
        with open(output_file, "w") as f:
            f.write(response.output)
