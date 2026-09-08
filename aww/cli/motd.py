import datetime
import json

import click
import rich
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessagesTypeAdapter
from pydantic_ai.models import Model
from rich.markdown import Markdown

from aww.cli import main
from aww.config import Settings
from aww.obsidian import Level
from aww.prompts import select_prompt_template
from aww.retro_gen import METRIC_FORMATTERS


def rewrite_yesterday_retrospective(content: str, llm_model: Model) -> str:
    """
    Rewrite yesterday's retrospective so relative references remain anchored in the past.
    """
    prompt = select_prompt_template(["motd_rewrite_yesterday.md"]).render()
    agent = Agent(model=llm_model, system_prompt=prompt, output_type=str)
    response = agent.run_sync([content])
    return response.output


def get_motd_context(
    vault,
    llm_model: Model | None = None,
    daily: bool = True,
    yesterday: bool = True,
    weekly: bool = True,
    memory: bool = True,
    ignored_headers: list[str] | None = None,
) -> list[str]:
    """
    Gather context for the MOTD prompt.
    """
    context = []
    if daily:
        daily_notes = vault.page(datetime.date.today(), Level.daily)
        if daily_notes:
            context.append(
                "=== DAILY NOTES ===\n" + daily_notes.content(ignored_headers=ignored_headers)
            )
            if fm := daily_notes.frontmatter():
                metrics = []
                for key, fmt in METRIC_FORMATTERS.items():
                    if (value := fm.get(key)) is not None:
                        metrics.append(fmt.format(value))
                if metrics:
                    context.append("=== TODAY'S METRICS ===\n" + "\n".join(metrics))
    if yesterday:
        yesterday_retro = vault.retrospective_page(
            datetime.date.today() - datetime.timedelta(days=1), Level.daily
        )
        if yesterday_retro:
            yesterday_content = yesterday_retro.content()
            if llm_model is not None:
                yesterday_content = rewrite_yesterday_retrospective(
                    yesterday_content, llm_model
                )
            context.append("=== YESTERDAY RETROSPECTIVE ===\n" + yesterday_content)
    if weekly:
        weekly_retro = vault.retrospective_page(datetime.date.today(), Level.weekly)
        if weekly_retro:
            context.append("=== WEEKLY RETROSPECTIVE ===\n" + weekly_retro.content())

        weekly_note = vault.page(datetime.date.today(), Level.weekly)
        if weekly_note:
            if goals := weekly_note.section("Weekly Goals"):
                context.append("=== WEEKLY GOALS ===\n" + goals)
    if memory:
        scratchpad = vault.page_by_name("aww-scratchpad")
        if scratchpad:
            context.append("=== AGENT MEMORIES ===\n" + scratchpad.content())
    return context


@main.command()
@click.option("--output-file", type=click.Path(), help="File to write the output to.")
@click.option("-d", "--daily", is_flag=True, help="Include daily note.")
@click.option(
    "-y", "--yesterday", is_flag=True, help="Include yesterday retrospective."
)
@click.option("-w", "--weekly", is_flag=True, help="Include weekly retrospective.")
@click.option("-m", "--memory", is_flag=True, help="Use memory (aww-scratchpad) to generate prompt.")
@click.option(
    "--plain-text",
    is_flag=True,
    default=False,
    help="Output plain text instead of markdown.",
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Show verbose output (prints user prompt)."
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Print the full LLM message history used to generate the MOTD.",
)
@click.pass_context
def motd(
    ctx, output_file, plain_text, daily, yesterday, weekly, memory, verbose, debug
):
    """Show a motivational message of the day."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    settings = ctx.obj.get("settings") or Settings()

    hour = datetime.datetime.now().hour
    part_of_day = "full"
    if hour in range(0, 4) or hour in range(21, 24):
        part_of_day = "night"
    elif hour in range(4, 7):
        part_of_day = "early_morning"
    elif hour in range(7, 12):
        part_of_day = "morning"
    elif hour in range(12, 15):
        part_of_day = "afternoon"
    elif hour in range(15, 18):
        part_of_day = "early_evening"
    elif hour in range(18, 21):
        part_of_day = "evening"

    prompt = select_prompt_template([f"motd.{part_of_day}.md", "motd.md"]).render()

    agent = Agent(model=llm_model, system_prompt=prompt)

    user_prompt = get_motd_context(
        vault,
        llm_model=llm_model,
        daily=daily,
        yesterday=yesterday,
        weekly=weekly,
        memory=memory,
        ignored_headers=settings.ignored_journal_headers,
    )

    user_prompt.append(
        f"Today, it is {datetime.datetime.now().strftime('%A %B %d %Y at %H:%M')}"
    )

    user_prompt.append("Write an impactful Message Of The Day (MOTD)")

    if verbose:
        for part in user_prompt:
            rich.print(part)

    response = agent.run_sync(user_prompt)
    if debug:
        rich.print_json(
            data=json.loads(
                ModelMessagesTypeAdapter.dump_json(response.all_messages()).decode(
                    "utf-8"
                )
            )
        )
    if plain_text:
        print(response.output)
    else:
        rich.print(Markdown(response.output))

    if output_file:
        with open(output_file, "w") as f:
            f.write(response.output)
