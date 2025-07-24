import asyncio
import calendar
import datetime
import enum
import os
import sys
import textwrap
from typing import Any

from pathlib import PosixPath

import click
import rich
import tqdm.asyncio
from aww import retro
from aww.obsidian import Vault, Level
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio, CallToolFunc, ToolResult
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.markdown import Markdown

vault: Vault
llm_model: Model



class Provider(enum.Enum):
    LOCAL = "local"
    GEMINI = "gemini"
    OPENAI = "openai"


class NoCachePolicyChoice(enum.Enum):
    ROOT = 'root'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'
    MTIME = 'mtime'


@click.group()
@click.option('--local_model', type=str, default='qwen/qwen3-30b-a3b')
@click.option('--local_url', type=str, default='http://localhost:1234/v1')
@click.option('--gemini_model', type=str, default='gemini-2.5-flash')
@click.option('--openai_model', type=str, default='o4-mini')
@click.option('-p', '--provider', type=click.Choice(Provider, case_sensitive=False), default='local')
@click.option('--vault_path', type=click.Path(), default="~/data/notes")
@click.option('--journal_dir', type=str, default='journal')
@click.option('--retrospectives_dir', type=str, default='retrospectives')
def main(provider, local_model, local_url, gemini_model, openai_model, vault_path, journal_dir, retrospectives_dir):
    global llm_model
    global vault
    match provider:
        case Provider.LOCAL:
            llm_model = OpenAIModel(model_name=local_model, provider=OpenAIProvider(base_url=local_url))
        case Provider.GEMINI:
            if "GEMINI_API_KEY" not in os.environ:
                print("Please set environment variable 'GEMINI_API_KEY'")
                sys.exit(1)
            llm_model = GeminiModel(model_name=gemini_model)
        case Provider.OPENAI:
            if "OPENAI_API_KEY" not in os.environ:
                print("Please set environment variable 'OPENAI_API_KEY'")
                sys.exit(1)
            llm_model = OpenAIModel(model_name=openai_model)
    vault_path = os.path.expanduser(vault_path)
    vault = Vault(PosixPath(vault_path), journal_dir, retrospectives_dir)


def do_retrospective(vault: Vault, dates: list[datetime.date], no_cache: list[NoCachePolicyChoice],
                     context_levels: list[Level],
                     level: Level, concurrency_limit: int):
    print("Generating", level.value, "retrospective from", dates[0], "to", dates[-1])
    print("NoCache policy:", ",".join(c.value for c in no_cache))
    print("Context:", ",".join(c.value for c in context_levels))
    print("Concurrency Limit:", concurrency_limit)

    cache_policies = []
    no_cache_levels = []
    for policy in no_cache:
        match policy:
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
    if no_cache_levels:
        cache_policies.append(retro.NoLevelsCachePolicy(levels=no_cache_levels))

    generator = retro.RecursiveRetrospectiveGenerator(llm_model, vault, dates, level, concurrency_limit)
    result = asyncio.run(
        generator.run(context_levels=context_levels, cache_policies=cache_policies, gather=tqdm.asyncio.tqdm.gather))
    if result:
        rich.print(Markdown(result.output))


@main.command(name="retro")
@click.argument('level', type=click.Choice(Level, case_sensitive=False))
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-n', '--no-cache', type=click.Choice(NoCachePolicyChoice, case_sensitive=False),
              multiple=True, help="No cache policy")
@click.option('-c', '--context', type=click.Choice(Level, case_sensitive=False),
              multiple=True, help="Context levels for retrospective")
@click.option('-C', '--concurrency-limit', type=click.IntRange(min=1), help="Concurrency limit")
@click.option('-y', '--yesterday', is_flag=True, default=False, help="Switch to previous date (only for daily level)")
def retrospectives(level: Level, date: datetime.datetime, no_cache: list[NoCachePolicyChoice], context: list[Level],
                   concurrency_limit: int, yesterday: bool):
    """Generate retrospective(s)."""
    dates: list[datetime.date]
    the_date = date.date()
    if yesterday:
        if level != Level.daily:
            click.echo("Error: --yesterday can only be used with daily level.", err=True)
            sys.exit(1)
        the_date = the_date - datetime.timedelta(days=1)

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

    match level:
        case Level.daily:
            dates = [the_date]
        case Level.weekly:
            dates = whole_week(the_date)
        case Level.monthly:
            dates = whole_month(the_date)
        case Level.yearly:
            dates = whole_year(the_date)
        case _:
            # Should not happen with click.Choice
            click.echo(f"Error: Unknown level '{level}'", err=True)
            sys.exit(1)

    do_retrospective(vault, dates, final_no_cache, final_context, level, final_concurrency_limit)


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
def chat(journal_cmd):
    """Interactive chat with LLM access to the user's vault."""
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


if __name__ == "__main__":
    main()
