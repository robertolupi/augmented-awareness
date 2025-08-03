import asyncio
import datetime

import click
import rich
from tqdm.asyncio import tqdm
from rich.markdown import Markdown

from aww import retro
from aww.cli import NoCachePolicyChoice, main
from aww.cli.utils import get_dates_for_level
from aww.obsidian import Level


@main.command(name="retro")
@click.argument("level", type=click.Choice(Level, case_sensitive=False))
@click.option(
    "-d", "--date", type=click.DateTime(), default=datetime.date.today().isoformat()
)
@click.option(
    "-n",
    "--no-cache",
    type=click.Choice(NoCachePolicyChoice, case_sensitive=False),
    multiple=True,
    help="Don't use cached results for the given level. Can be specified multiple times.",
)
@click.option(
    "-c",
    "--context",
    type=click.Choice(Level, case_sensitive=False),
    multiple=True,
    help="Which levels of retrospectives to include as context. Can be specified multiple times.",
)
@click.option(
    "-C",
    "--concurrency-limit",
    type=click.IntRange(min=1),
    help="How many concurrent LLM API calls to make.",
)
@click.option(
    "-y",
    "--yesterday",
    is_flag=True,
    default=False,
    help="Use yesterday's date (only for daily level).",
)
@click.option("--output-file", type=click.Path(), help="File to write the output to.")
@click.option(
    "--plain-text",
    is_flag=True,
    default=False,
    help="Output plain text instead of markdown.",
)
@click.pass_context
def retrospectives(
    ctx,
    level: Level,
    date: datetime.datetime,
    no_cache: list[NoCachePolicyChoice],
    context: list[Level],
    concurrency_limit: int | None,
    yesterday: bool,
    output_file: str | None,
    plain_text: bool,
):
    """Generate retrospective(s)."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    dates = get_dates_for_level(level, date, yesterday)

    # Set defaults based on level
    final_no_cache = list(no_cache)
    final_context = list(context)
    final_concurrency_limit = concurrency_limit or 10

    if not final_no_cache:
        final_no_cache = [NoCachePolicyChoice.ROOT, NoCachePolicyChoice.MTIME]
    if not final_context:
        final_context = []
        for l in Level:
            if l == level:
                break
            final_context.append(l)

    print("Generating", level.value, "retrospective from", dates[0], "to", dates[-1])
    print("NoCache policy:", ",".join(c.value for c in final_no_cache))
    print("Context:", ",".join(c.value for c in final_context))
    print("Concurrency Limit:", final_concurrency_limit)

    cache_policies = []
    no_cache_levels = []
    for policy in final_no_cache:
        match policy:
            case NoCachePolicyChoice.CACHE:
                # No op, but clears final_no_cache defaults
                pass
            case NoCachePolicyChoice.ROOT:
                cache_policies.append(retro.NoRootCachePolicy())
            case NoCachePolicyChoice.DAILY:
                no_cache_levels.append(Level.daily)
            case NoCachePolicyChoice.WEEKLY:
                no_cache_levels.append(Level.weekly)
            case NoCachePolicyChoice.MONTHLY:
                no_cache_levels.append(Level.monthly)
            case NoCachePolicyChoice.YEARLY:
                no_cache_levels.append(Level.yearly)
            case NoCachePolicyChoice.MTIME:
                cache_policies.append(retro.ModificationTimeCachePolicy())
            case NoCachePolicyChoice.ONE_HOUR:
                cache_policies.append(
                    retro.TooOldCachePolicy(
                        datetime.datetime.now() - datetime.timedelta(hours=1)
                    )
                )
    if no_cache_levels:
        cache_policies.append(retro.NoLevelsCachePolicy(levels=no_cache_levels))

    generator = retro.RecursiveRetrospectiveGenerator(
        llm_model, vault, dates, level, final_concurrency_limit
    )
    result = asyncio.run(
        generator.run(
            context_levels=final_context,
            cache_policies=cache_policies,
            gather=tqdm.gather,
        )
    )
    if result:
        output_content = result.output
        if output_file:
            with open(output_file, "w") as f:
                f.write(output_content)
            print(f"Output written to {output_file}")
        if plain_text:
            print(output_content)
        else:
            rich.print(Markdown(output_content))
