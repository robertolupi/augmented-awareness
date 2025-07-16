import datetime
from collections import OrderedDict

import click
import rich

from rich.markdown import Markdown

from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.gemini import GeminiModel

from aww.config import Settings
from aww.obsidian import Vault
from aww import retro

settings = Settings()

llm_model : Model

@click.group()
@click.option('--local_model', type=str, default='qwen/qwen3-30b-a3b')
@click.option('--local_provider', type=str, default='http://localhost:1234/v1')
@click.option('--gemini_model', type=str, default='gemini-2.5-flash')
@click.option('-m', '--model', type=str, default='local')
def main(model, local_model, local_provider, gemini_model):
    global llm_model
    match model:
        case "local":
            provider = OpenAIProvider(base_url=local_provider)
            llm_model = OpenAIModel(model_name=local_model, provider=provider)
        case "gemini":
            llm_model = GeminiModel(model_name=gemini_model)
            


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
def daily_retro(date: datetime.date):
    """Daily retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)
    agent = retro.DailyRetrospectiveAgent(llm_model, vault)
    result = agent.run_sync(date)
    rich.print(Markdown(result.output))


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
def weekly_retro(date: datetime.date):
    """Weekly retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)
    past_week = [date - datetime.timedelta(days=i) for i in range(7, 0, -1)]    
    agent = retro.WeeklyRetrospectiveAgent(llm_model, vault)
    result = agent.run_sync(past_week)
    rich.print(Markdown(result.output))


if __name__ == "__main__":
    main()
