import asyncio
import calendar
import datetime
import enum
import os
import sys
import textwrap
from typing import Any

from pathlib import Path

import click
import rich
import tqdm.asyncio

import aww.obsidian
from aww import retro
from aww import config
from aww.obsidian import Vault, Level
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio, CallToolFunc, ToolResult
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.markdown import Markdown

class Provider(enum.Enum):
    LOCAL = "local"
    GEMINI = "gemini"
    OPENAI = "openai"


class NoCachePolicyChoice(enum.Enum):
    CACHE = 'do_cache'
    ROOT = 'root'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'
    MTIME = 'mtime'
    ONE_HOUR = '1h'


settings = config.Settings()


@click.group()
@click.option('--local_model', type=str, default=settings.local_model)
@click.option('--local_url', type=str, default=settings.local_base_url)
@click.option('--gemini_model', type=str, default=settings.gemini_model)
@click.option('--openai_model', type=str, default=settings.openai_model)
@click.option('-p', '--provider', type=click.Choice(Provider, case_sensitive=False), default='local')
@click.option('--vault_path', type=click.Path(), default=settings.vault_path)
@click.option('--journal_dir', type=str, default=settings.journal_dir)
@click.option('--retrospectives_dir', type=str, default=settings.retrospectives_dir)
@click.pass_context
def main(ctx, provider, local_model, local_url, gemini_model, openai_model, vault_path, journal_dir, retrospectives_dir):
    llm_model = make_model(gemini_model, local_model, local_url, openai_model, provider)
    vault_path = os.path.expanduser(vault_path)
    vault = Vault(Path(vault_path), journal_dir, retrospectives_dir)
    ctx.obj = {
        'llm_model': llm_model,
        'vault': vault,
        'settings': settings,
    }


def make_model(gemini_model, local_model, local_url, openai_model, provider):
    match provider:
        case Provider.LOCAL:
            model = OpenAIModel(model_name=local_model, provider=OpenAIProvider(base_url=local_url))
        case Provider.GEMINI:
            if "GEMINI_API_KEY" not in os.environ:
                raise click.ClickException(
                    "Please set environment variable GEMINI_API_KEY"
                )
            model = GeminiModel(model_name=gemini_model)
        case Provider.OPENAI:
            if "OPENAI_API_KEY" not in os.environ:
                raise click.ClickException(
                    "Please set environment variable OPENAI_API_KEY"
                )
            model = OpenAIModel(model_name=openai_model)
        case _:
            raise click.ClickException(f"Unknown provider: {provider}")
    return model


def whole_year(the_date: datetime.date) -> list[datetime.date]:
    year = the_date.year
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    return dates


def whole_month(the_date: datetime.date) -> list[datetime.date]:
    year = the_date.year
    month = the_date.month
    num_days = calendar.monthrange(year, month)[1]
    dates = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
    return dates


def whole_week(the_date: datetime.date) -> list[datetime.date]:
    """Returns the weekly dates (Mon to Friday) for the week that contains the given date."""
    monday = the_date - datetime.timedelta(days=the_date.weekday())
    return [monday + datetime.timedelta(days=i) for i in range(7)]


def get_dates_for_level(level: Level, date: datetime.datetime, yesterday: bool) -> list[datetime.date]:
    """Calculates the list of dates for a given level, date, and yesterday flag."""
    the_date = date.date()
    if yesterday:
        if level != Level.daily:
            raise click.ClickException(
                "--yesterday can only be used with daily level"
            )
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


@main.command(name="retro")
@click.argument('level', type=click.Choice(Level, case_sensitive=False))
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-n', '--no-cache', type=click.Choice(NoCachePolicyChoice, case_sensitive=False),
              multiple=True, help="Don't use cached results for the given level. Can be specified multiple times.")
@click.option('-c', '--context', type=click.Choice(Level, case_sensitive=False),
              multiple=True, help="Which levels of retrospectives to include as context. Can be specified multiple times.")
@click.option('-C', '--concurrency-limit', type=click.IntRange(min=1), help="How many concurrent LLM API calls to make.")
@click.option('-y', '--yesterday', is_flag=True, default=False, help="Use yesterday's date (only for daily level).")
@click.pass_context
def retrospectives(ctx, level: Level, date: datetime.datetime, no_cache: list[NoCachePolicyChoice], context: list[Level],
                   concurrency_limit: int, yesterday: bool):
    """Generate retrospective(s)."""
    vault = ctx.obj['vault']
    llm_model = ctx.obj['llm_model']
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
                cache_policies.append(retro.TooOldCachePolicy(datetime.datetime.now() - datetime.timedelta(hours=1)))
    if no_cache_levels:
        cache_policies.append(retro.NoLevelsCachePolicy(levels=no_cache_levels))

    generator = retro.RecursiveRetrospectiveGenerator(llm_model, vault, dates, level, final_concurrency_limit)
    result = asyncio.run(
        generator.run(context_levels=final_context, cache_policies=cache_policies, gather=tqdm.asyncio.tqdm.gather))
    if result:
        rich.print(Markdown(result.output))


async def process_tool_call(
        ctx: RunContext[int],
        call_tool: CallToolFunc,
        name: str,
        tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    print(f"Tool call {name}")
    return await call_tool(name, tool_args, {'deps': ctx.deps})


@main.command(name="chat")
@click.option('-j', '--journal_cmd', type=str, default="./journal")
@click.pass_context
def chat(ctx, journal_cmd):
    """Interactive chat with LLM access to the user's vault."""
    vault = ctx.obj['vault']
    llm_model = ctx.obj['llm_model']
    server = MCPServerStdio(
        journal_cmd,
        args=["--vault", str(vault.path), "mcp"],
        process_tool_call=process_tool_call,
    )
    ask_agent = Agent(model=llm_model, toolsets=[server])

    @ask_agent.system_prompt
    def system_prompt():
        return textwrap.dedent("""You are a helpful holistic assistant. 
        Read the user retrospectives, weekly journal and pages as needed, then answer the user question.
        Call at most one tool at a time.
        """)

    ask_agent.to_cli_sync(prog_name="aww")


@main.command(name="ask")
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-f', '--prompt_file', type=click.Path(exists=True), default=None)
@click.option('-c', '--context', type=click.Choice(Level, case_sensitive=False),
              multiple=True, help="Context levels for retrospective",
              default=[Level.daily, Level.weekly, Level.monthly, Level.yearly])
@click.argument('level', type=click.Choice(Level, case_sensitive=False))
@click.argument('prompt', type=str)
@click.option('-y', '--yesterday', is_flag=True, default=False, help="Switch to previous date (only for daily level)")
@click.option('-v', '--verbose', is_flag=True, default=False, help="Be verbose (show all sources)")
@click.pass_context
def ask(ctx, date, yesterday, context, level, prompt, prompt_file, verbose):
    """Concatenate retrospectives and ask a question."""
    vault = ctx.obj['vault']
    llm_model = ctx.obj['llm_model']
    dates = get_dates_for_level(level, date, yesterday)

    if prompt_file:
        prompt = open(prompt_file, 'r').read()

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
    rich.print(Markdown(result.output))


@main.command(name="rewrite_prompt")
@click.option('--critique_local_model', type=str)
@click.option('--critique_local_url', type=str)
@click.option('--critique_gemini_model', type=str)
@click.option('--critique_openai_model', type=str)
@click.option('-P', '--critique_provider', type=click.Choice(Provider, case_sensitive=False), default='local')
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-c', '--context', type=click.Choice(Level, case_sensitive=False),
              multiple=True, help="Context levels for retrospective",
              default=[Level.daily, Level.weekly, Level.monthly, Level.yearly])
@click.argument('level', type=click.Choice(Level, case_sensitive=False))
@click.option('-y', '--yesterday', is_flag=True, default=False, help="Switch to previous date (only for daily level)")
@click.pass_context
def rewrite_prompt(ctx, critique_local_model, critique_local_url, critique_gemini_model, critique_openai_model,
                   critique_provider, date, yesterday, context, level):
    vault = ctx.obj['vault']
    llm_model = ctx.obj['llm_model']
    settings = ctx.obj['settings']
    critique_local_model = critique_local_model or settings.local_model
    critique_local_url = critique_local_url or settings.local_base_url
    critique_gemini_model = critique_gemini_model or settings.gemini_model
    critique_openai_model = critique_openai_model or settings.openai_model
    dates = get_dates_for_level(level, date, yesterday)

    tree = aww.obsidian.build_retrospective_tree(vault, dates)
    retro_page = vault.retrospective_page(dates[0], level)
    node = tree[retro_page]
    sources = [n for n in node.sources if n.level in context]
    if node.level in context:
        sources.insert(0, node)
    content = [s.retro_page.content() for s in sources if s.retro_page]
    if level == Level.daily:
        page_content = asyncio.run(aww.retro.page_content(node))
        content.insert(0, page_content)

    critique_model = make_model(critique_gemini_model, critique_local_model, critique_local_url, critique_openai_model,
                                critique_provider)
    critique_agent = Agent(model=critique_model, output_type=str)

    @critique_agent.system_prompt
    def critique():
        return textwrap.dedent("""
        You are an expert at writing LLM prompts. You will receive:
        1) the prompt
        2) the output
        3) a series of input messages
        Your job is to write a revised prompt that is more performant.
        Write only the revised prompt in full, in markdown format.
        """)

    prompt_file = Path(aww.__file__).parent / "retro" / f"{level.value}.md"
    prompt = prompt_file.read_text()

    gen_agent = Agent(model=llm_model, system_prompt=prompt)

    async def do_critique():
        gen_result = await gen_agent.run(user_prompt=content)
        gen_output = gen_result.output
        critique_result = await critique_agent.run(user_prompt=[prompt, gen_output] + content)
        return critique_result.output

    result = asyncio.run(do_critique())
    rich.print(Markdown(result))
    prompt_file.write_text(result)


if __name__ == "__main__":
    main()
