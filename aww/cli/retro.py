import asyncio
import datetime
import enum

import click
import rich
from rich.markdown import Markdown
from tqdm.asyncio import tqdm

from aww import retro, retro_gen
from aww.cli import main
from aww.obsidian import Level
from aww.retro import whole_month, whole_week, whole_year


class NoCachePolicyChoice(enum.Enum):
    CACHE = "do_cache"
    ALL = "all"  # no cache at all
    ROOT = "root"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    MTIME = "mtime"
    ONE_HOUR = "1h"


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
    if yesterday:
        date = date - datetime.timedelta(days=1)

    sel = retro.Selection(vault, date, level)

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

    print(
        "Generating",
        level.value,
        "retrospective from",
        sel.dates[0],
        "to",
        sel.dates[-1],
    )
    print("NoCache policy:", ",".join(c.value for c in final_no_cache))
    print("Context:", ",".join(c.value for c in final_context))
    print("Concurrency Limit:", final_concurrency_limit)

    cache_policies = get_cache_policies(final_no_cache)

    generator = retro_gen.RecursiveGenerator(
        llm_model, sel, final_concurrency_limit
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


def get_cache_policies(
    no_cache_choices: list[NoCachePolicyChoice],
) -> list[retro.CachePolicy]:
    """
    Converts a list of NoCachePolicyChoice enums into a list of CachePolicy objects.
    """
    cache_policies = []
    no_cache_levels = []
    for policy in no_cache_choices:
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
            case NoCachePolicyChoice.ALL:
                cache_policies.extend(
                    [retro.NoRootCachePolicy(),
                     retro.ModificationTimeCachePolicy()]
                )
                no_cache_levels.extend(
                    [
                        Level.daily,
                        Level.weekly,
                        Level.monthly,
                        Level.yearly,
                    ]
                )

    if no_cache_levels:
        cache_policies.append(retro.NoLevelsCachePolicy(levels=no_cache_levels))
    return cache_policies


def get_dates_for_level(
    level: Level, date: datetime.datetime, yesterday: bool
) -> list[datetime.date]:
    """Calculates the list of dates for a given level, date, and yesterday flag."""
    the_date = date.date()
    if yesterday:
        if level != Level.daily:
            raise click.ClickException("--yesterday can only be used with daily level")
        the_date = the_date - datetime.timedelta(days=1)

    match level:
        case Level.daily:
            return [the_date]
        case Level.weekly:
            return whole_week(the_date)
        case Level.monthly:
            return whole_month(the_date)
        case Level.yearly:
            return whole_year(the_date)
        case _:
            # Should not happen with click.Choice
            raise click.ClickException(f"Unknown level '{level}'")
