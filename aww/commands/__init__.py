import os

import click
import rich

from aww.commands import config
from aww.commands import datastore
from aww.commands import obsidian
from aww.commands import schedule
from aww import settings
from aww import context

import logfire


@click.group()
@click.option(
    "config_file",
    "--config-file",
    "-c",
    type=click.Path(
        file_okay=True, dir_okay=False, writable=True, readable=True, resolve_path=True
    ),
)
@click.option("show_config", "--show-config", is_flag=True)
def main(config_file: str | None, show_config: bool = False):
    if config_file:
        settings.CONFIG_FILE = config_file

    if "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT" in os.environ:
        logfire.configure(service_name="aww", send_to_logfire=False)

    if show_config:
        cfg = settings.Settings()
        rich.print(cfg)

    context.initialize()


main.add_command(config.commands)
main.add_command(datastore.commands)
main.add_command(obsidian.commands)
main.add_command(schedule.commands)

if __name__ == "__main__":
    main()
