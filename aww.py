import datetime
from collections import OrderedDict

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
        result = retro.daily_agent.run_sync(page.content())
        rich.print(Markdown(result.output))


@main.command()
@click.option('-d', '--date', type=click.DateTime(), default=datetime.date.today().isoformat())
def weekly_retro(date: datetime.date):
    """Weekly retrospective."""
    vault = Vault(settings.vault_path, settings.journal_dir)
    past_week = [date - datetime.timedelta(days=i) for i in range(7, 0, -1)]
    daily = OrderedDict()
    for d in past_week:
        page = vault.daily_page(d)
        if page:
            result = retro.daily_agent.run_sync(page.content())
            daily[d] = result.output
    weekly_summary = []
    for d, result in daily.items():
        weekly_summary.extend([f"# Daily summary for {d.isoformat()}\n", result])
        rich.print(Markdown(f"# Daily summary for {d.isoformat()}\n"))
        rich.print(Markdown(result))
    result = retro.weekly_agent.run_sync('\n'.join(weekly_summary))
    rich.print(Markdown("# Weekly summary\n"))
    rich.print(Markdown(result.output))



if __name__ == "__main__":
    main()
