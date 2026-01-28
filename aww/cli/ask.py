import datetime

import click
import rich
from pydantic_ai import Agent
from rich.markdown import Markdown
from tqdm.asyncio import tqdm

from aww import retro
import aww.ask
from aww.cli import main
from aww.obsidian import Level


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
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    default=False,
    help="Recursive map-reduce over journal entries.",
)
@click.option(
    "-n",
    "--no-cache",
    is_flag=True,
    default=False,
    help="Don't use cached results for the current query.",
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
    recursive,
    no_cache,
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
    if yesterday:
        date = date - datetime.timedelta(days=1)

    if prompt_file:
        prompt = prompt + "\n" + open(prompt_file, "r").read()

    # Convert datetime to date for the logic function
    query_date = date.date() if isinstance(date, datetime.datetime) else date

    cache_policies = None
    if no_cache:
        cache_policies = [retro.NoRootCachePolicy(), retro.NoLevelsCachePolicy(list(Level))]

    output_content = aww.ask.ask_question(
        vault=vault,
        llm_model=llm_model,
        date=query_date,
        level=level,
        prompt=prompt,
        context_levels=list(context),
        verbose=verbose,
        recursive=recursive,
        cache_policies=cache_policies,
        gather=tqdm.gather,
    )

    if output_file:
        with open(output_file, "w") as f:
            f.write(output_content)
        print(f"Output written to {output_file}")
    if plain_text:
        print(output_content)
    else:
        rich.print(Markdown(output_content))
