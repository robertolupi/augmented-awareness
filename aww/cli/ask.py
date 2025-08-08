import datetime

import click
import rich
from rich.markdown import Markdown

import aww.obsidian
from aww.cli import main
from aww.cli.utils import get_dates_for_level
from aww.obsidian import Level
from pydantic_ai import Agent


@main.command(name="ask")
@click.option(
    "-d", "--date", type=click.DateTime(), default=datetime.date.today().isoformat()
)
@click.option("-f", "--prompt-file", type=click.Path(exists=True), default=None)
@click.option(
    "-c",
    "--context",
    type=click.Choice(Level, case_sensitive=False),
    multiple=True,
    help="Context levels for retrospective",
    default=[Level.daily, Level.weekly, Level.monthly, Level.yearly],
)
@click.argument("level", type=click.Choice(Level, case_sensitive=False))
@click.argument("prompt", type=str)
@click.option(
    "-y",
    "--yesterday",
    is_flag=True,
    default=False,
    help="Switch to previous date (only for daily level)",
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Be verbose (show all sources)"
)
@click.option("--output-file", type=click.Path(), help="File to write the output to.")
@click.option(
    "--plain-text",
    is_flag=True,
    default=False,
    help="Output plain text instead of markdown.",
)
@click.pass_context
def ask(
    ctx,
    date,
    yesterday,
    context,
    level,
    prompt,
    prompt_file,
    verbose,
    output_file,
    plain_text,
):
    """Concatenate retrospectives and ask a question."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    dates = get_dates_for_level(level, date, yesterday)

    if prompt_file:
        prompt = open(prompt_file, "r").read()

    ask_agent = Agent(model=llm_model, system_prompt=prompt)

    tree = aww.obsidian.build_retrospective_tree(vault, dates)
    retro_page = vault.retrospective_page(dates[0], level)
    node = tree[retro_page]
    sources = [n for n in node.sources if n.level in context]
    if node.level in context:
        sources.insert(0, node)
    sources = [s for s in sources if s.retro_page]
    if verbose:
        rich.print("Sources", [n.retro_page.name for n in sources])
    retros = [n.retro_page.content() for n in sources]

    result = ask_agent.run_sync(user_prompt=retros)
    output_content = result.output
    if output_file:
        with open(output_file, "w") as f:
            f.write(output_content)
        print(f"Output written to {output_file}")
    if plain_text:
        print(output_content)
    else:
        rich.print(Markdown(output_content))
