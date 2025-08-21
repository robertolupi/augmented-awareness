import datetime

import click
import rich

from aww.cli import main
from aww.obsidian import Page, Level

one_week_ago = datetime.datetime.now() - datetime.timedelta(weeks=1)
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)


@main.command()
@click.option(
    "-s",
    "--start-date",
    metavar="YYYY-MM-DD",
    default=one_week_ago.strftime("%Y-%m-%d"),
    type=click.DateTime(),
)
@click.option(
    "-e",
    "--end-date",
    metavar="YYYY-MM-DD",
    default=yesterday.strftime("%Y-%m-%d"),
    type=click.DateTime(),
)
@click.option("-t", "--template", metavar="FILE", default="templates/daily.md")
@click.pass_context
def tasks_cleanup(ctx, start_date, end_date, template):
    """Cleanup AWW tasks."""
    vault = ctx.obj["vault"]

    template_page = Page(vault.path / template)
    if not template_page:
        click.secho("Template file not found", fg="red")
        return

    template_tasks = template_page.tasks().description.to_list()

    date = start_date
    while date < end_date:
        click.secho(f"Cleaning {date}...", fg="green")
        page = vault.page(date, Level.daily)
        if not page:
            click.secho("Page not found", fg="red")

        page_lines = page.path.open().readlines()

        page_tasks = page.tasks()
        for index, row in page_tasks.iterrows():
            if row["status"] == " " and row["description"] in template_tasks:
                page_lines[index] = page_lines[index].replace("[ ]", "[-]")

        with page.path.open("w") as f:
            f.writelines(page_lines)

        date = date + datetime.timedelta(days=1)
