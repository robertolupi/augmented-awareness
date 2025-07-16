import asyncio
import calendar
import datetime
import enum
from collections import OrderedDict

import click
import rich
import tqdm.asyncio

from rich.markdown import Markdown

from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.gemini import GeminiModel

from aww.config import Settings
from aww.obsidian import Vault
from aww import retro

settings = Settings()

llm_model: Model


class ModelChoice(enum.Enum):
    LOCAL = "local"
    GEMINI = "gemini"
    OPENAI = "openai"


@click.group()
@click.option('--local_model', type=str, default='qwen/qwen3-30b-a3b')
@click.option('--local_provider', type=str, default='http://localhost:1234/v1')
@click.option('--gemini_model', type=str, default='gemini-2.5-flash')
@click.option('--openai_model', type=str, default='o4-mini')
@click.option('-m', '--model', type=click.Choice(ModelChoice, case_sensitive=False), default='local')
def main(model, local_model, local_provider, gemini_model, openai_model):
    global llm_model
    match model:
        case ModelChoice.LOCAL:
            provider = OpenAIProvider(base_url=local_provider)
            llm_model = OpenAIModel(model_name=local_model, provider=provider)
        case ModelChoice.GEMINI:
            llm_model = GeminiModel(model_name=gemini_model)
        case ModelChoice.OPENAI:
            llm_model = OpenAIModel(model_name=openai_model)


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('--no-cache', type=int, default=0, help="Do not use cached retrospectives.")
def daily_retro(date: datetime.datetime, no_cache: int):
    """Daily retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)
    agent = retro.DailyRetrospectiveAgent(llm_model, vault)
    result = asyncio.run(agent.run(date.date(), no_cache=no_cache))
    if result:
        rich.print(Markdown(result.output))


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('--no-cache', type=int, default=0, help="Do not use cached retrospectives.")
def weekly_retro(date: datetime.datetime, no_cache: int):
    """Weekly retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)
    past_week = [date.date() - datetime.timedelta(days=i) for i in range(7, 0, -1)]
    agent = retro.WeeklyRetrospectiveAgent(llm_model, vault)
    result = asyncio.run(agent.run(past_week, gather=tqdm.asyncio.tqdm.gather, no_cache=no_cache))
    if result:
        rich.print(Markdown(result.output))


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('--no-cache', type=int, default=0, help="Do not use cached retrospectives.")
def monthly_retro(date: datetime.datetime, no_cache: int):
    """Monthly retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)

    year = date.year
    month = date.month
    num_days = calendar.monthrange(year, month)[1]
    days_in_month = [datetime.date(year, month, day) for day in range(1, num_days + 1)]

    agent = retro.MonthlyRetrospectiveAgent(llm_model, vault)
    result = asyncio.run(agent.run(days_in_month, gather=tqdm.asyncio.tqdm.gather, no_cache=no_cache))
    if result:
        rich.print(Markdown(result.output))


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
@click.option('--no-cache', type=int, default=0, help="Do not use cached retrospectives.")
def yearly_retro(date: datetime.datetime, no_cache: int):
    """Yearly retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)

    year = date.year
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    days_in_year = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    agent = retro.YearlyRetrospectiveAgent(llm_model, vault)
    result = asyncio.run(agent.run(days_in_year, gather=tqdm.asyncio.tqdm.gather, no_cache=no_cache))
    if result:
        rich.print(Markdown(result.output))


if __name__ == "__main__":
    main()
