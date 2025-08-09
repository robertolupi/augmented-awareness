import datetime

import click
import rich
from pydantic_ai import Agent
from rich.markdown import Markdown

from aww import retro
from aww.cli import main
from aww.obsidian import Level, Page


@main.command()
@click.option(
    "-d", "--date", type=click.DateTime(), default=datetime.date.today().isoformat()
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
def compare(ctx: click.Context, date: datetime.datetime, level: Level, yesterday: bool):
    """Compare multiple generated retrospective pages, and output merged results."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    if yesterday:
        date = date - datetime.timedelta(days=1)

    sel = retro.Selection(vault, date, level)
    alternative_retros = alternatives(sel.root.retro_page)
    alternatives_content = [a.content() for a in alternative_retros]
    rich.print(alternative_retros)
    if not alternative_retros:
        return

    agent = Agent(
        model=llm_model,
        system_prompt="Task: Compare and adjudicate multiple summaries.",
    )

    configuration = """
EVALUATE
constraints:
  max_claims_per_section: 5
  min_consensus_k: 2
  max_examples_per_divergence: 3
"""

    agent_result = agent.run_sync(
        user_prompt=alternatives_content + [configuration],
        # output_type=AdjudicatorOutput,
    )
    rich.print(Markdown(agent_result.output))


def alternatives(page: Page) -> list[Page]:
    results = []
    for path in page.path.parent.glob(page.name + "*.md"):
        results.append(Page(path, page.level))
    return results
