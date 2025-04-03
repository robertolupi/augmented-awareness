import click
import rich

from aww.commands import config
from aww.commands import obsidian
from aww import settings


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

    if show_config:
        cfg = settings.Settings()
        rich.print(cfg)


main.add_command(config.commands)
main.add_command(obsidian.commands)

if __name__ == "__main__":
    main()
