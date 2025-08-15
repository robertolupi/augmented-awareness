import datetime
from pathlib import Path

import click

import rich
from rich.markdown import Markdown
import aww
from aww.cli import main

from pydantic_ai import Agent

from aww.obsidian import Level
from aww.prompts import select_prompt_template


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

    now = datetime.datetime.now()
    if now.time() < datetime.time(7, 0):
        part_of_day = "early"
    elif now.time() < datetime.time(12, 0):
        part_of_day = "morning"
    if now.time() < datetime.time(14, 0):
        part_of_day = "lunch"
    if now.time() < datetime.time(19, 0):
        part_of_day = "afternoon"
    if now.time() < datetime.time(21, 0):
        part_of_day = "evening"
    if now.time() < datetime.time(23, 0):
        part_of_day = "night"

    prompt = select_prompt_template([f"motd.{part_of_day}.md", "motd.md"]).render()

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

    user_prompt += "Write an impactful Message Of The Day (MOTD)"

    response = agent.run_sync(user_prompt)
    if plain_text:
        print(response.output)
    else:
        rich.print(Markdown(response.output))

    if output_file:
        with open(output_file, "w") as f:
            f.write(response.output)
