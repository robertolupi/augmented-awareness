import datetime

import click
import rich

from rich.markdown import Markdown

from aww.config import Settings
from aww.obsidian import Vault
from aww import retro

settings = Settings()


@click.group()
def main():
    pass


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
def daily_retro(date: datetime.date):
    """Daily retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)
    page = vault.daily_page(date)
    if page:
        result = retro.agent.run_sync(page.content())
        rich.print(Markdown(result.output))

if __name__ == "__main__":
    main()
