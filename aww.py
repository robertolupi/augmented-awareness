import asyncio
import calendar
import datetime
import enum
import sys
from collections import OrderedDict
from pickle import FALSE

import click
import rich
import tqdm.asyncio

from rich.markdown import Markdown

from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.gemini import GeminiModel

from aww.config import Settings
from aww.obsidian import Vault, Level
from aww import retro
import os
import sys

settings = Settings()

vault: Vault
llm_model: Model


class ModelChoice(enum.Enum):
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
@click.option('--local_provider', type=str, default='http://localhost:1234/v1')
@click.option('--gemini_model', type=str, default='gemini-2.5-flash')
@click.option('--openai_model', type=str, default='o4-mini')
@click.option('-m', '--model', type=click.Choice(ModelChoice, case_sensitive=False), default='local')
def main(model, local_model, local_provider, gemini_model, openai_model):
    global llm_model
    global vault
    match model:
        case ModelChoice.LOCAL:
            provider = OpenAIProvider(base_url=local_provider)
            llm_model = OpenAIModel(model_name=local_model, provider=provider)
        case ModelChoice.GEMINI:
            if "GEMINI_API_KEY" not in os.environ:
                print("Please set environment variable 'GEMINI_API_KEY'")
                sys.exit(1)
            llm_model = GeminiModel(model_name=gemini_model)
        case ModelChoice.OPENAI:
            if "OPENAI_API_KEY" not in os.environ:
                print("Please set environment variable 'OPENAI_API_KEY'")
                sys.exit(1)
            llm_model = OpenAIModel(model_name=openai_model)
    vault = Vault(settings.vault_path, settings.journal_dir, settings.retrospectives_dir)


def do_retrospective(vault: Vault, dates: list[datetime.date], no_cache: list[NoCachePolicyChoice],
                     context_levels: list[Level],
                     level: Level, concurrency_limit: int):
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


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-n', '--no-cache', type=click.Choice(NoCachePolicyChoice, case_sensitive=False),
              default=['root'], help="No cache policy", multiple=True)
@click.option('-y', '--yesterday', is_flag=True, default=False, help="Switch to previous date")
def daily_retro(date: datetime.datetime, no_cache: list[NoCachePolicyChoice], yesterday: bool):
    """Daily retrospective."""
    if yesterday:
        dates = [date.date() - datetime.timedelta(days=1)]
    else:
        dates = [date.date()]
    do_retrospective(vault, dates, no_cache, [], Level.daily, 10)


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-n', '--no-cache', type=click.Choice(NoCachePolicyChoice, case_sensitive=False),
              default=['root', 'mtime'], help="No cache policy", multiple=True)
def weekly_retro(date: datetime.datetime, no_cache: list[NoCachePolicyChoice]):
    """Weekly retrospective."""
    past_week = [date.date() - datetime.timedelta(days=i) for i in range(7, 0, -1)]
    do_retrospective(vault, past_week, no_cache, [Level.daily], Level.weekly, 7)


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-n', '--no-cache', type=click.Choice(NoCachePolicyChoice, case_sensitive=False),
              default=['root', 'mtime'], help="No cache policy", multiple=True)
@click.option('-c', '--context', type=click.Choice(retro.Level, case_sensitive=False), default=['daily', 'weekly'],
              multiple=True)
@click.option('-C', '--concurrency-limit', type=click.IntRange(min=1), default=10)
def monthly_retro(date: datetime.datetime, no_cache: list[NoCachePolicyChoice], context: list[retro.Level],
                  concurrency_limit: int):
    """Monthly retrospective."""
    year = date.year
    month = date.month
    num_days = calendar.monthrange(year, month)[1]
    days_in_month = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
    do_retrospective(vault, days_in_month, no_cache, context, Level.monthly, concurrency_limit)


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('-n', '--no-cache', type=click.Choice(NoCachePolicyChoice, case_sensitive=False),
              default=['root', 'mtime'], help="No cache policy", multiple=True)
@click.option('-c', '--context', type=click.Choice(retro.Level, case_sensitive=False),
              default=['daily', 'weekly', 'monthly'],
              multiple=True)
@click.option('-C', '--concurrency-limit', type=click.IntRange(min=1), default=10)
def yearly_retro(date: datetime.datetime, no_cache: list[NoCachePolicyChoice], context: list[retro.Level],
                 concurrency_limit: int):
    """Yearly retrospective."""
    year = date.year
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    days_in_year = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    do_retrospective(vault, days_in_year, no_cache, context, Level.yearly, concurrency_limit)


if __name__ == "__main__":
    main()
