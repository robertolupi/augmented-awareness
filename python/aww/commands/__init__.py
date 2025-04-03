import pathlib

import click
import platformdirs
import rich
import tomlkit
import tomlkit.exceptions

from aww.commands import config
from aww.commands import obsidian

from pyarrow import fs


@click.group()
@click.option(
    "config_file",
    "--config-file",
    "-c",
    type=click.Path(
        file_okay=True, dir_okay=False, writable=True, readable=True, resolve_path=True
    ),
)
@click.option("app_name", "--app-name", "-a", default="aww")
@click.option("app_author", "--app-author", "-A", default="rlupi")
@click.option("show_config", "--show-config", is_flag=True)
def main(
    config_file: str | None, app_name: str, app_author: str, show_config: bool = False
):
    if config_file:
        config.path = pathlib.Path(config_file)
    else:
        config.path = (
            pathlib.Path(platformdirs.user_config_dir(app_name, app_author))
            / "config.toml"
        )
    if config.path.exists() and config.path.is_file():
        try:
            config.configuration = tomlkit.parse(config.path.read_text())
        except tomlkit.exceptions.ParseError as e:
            rich.print(config.path, e)

    if "data" in config.configuration and "uri" in config.configuration["data"]:
        config.filesystem = fs.FileSystem.from_uri(config.configuration["data"]["uri"])
    else:
        data_path = (
            platformdirs.user_data_path(app_name, app_author) / "data"
        ).resolve()
        data_path.mkdir(parents=True, exist_ok=True)
        config.filesystem = fs.SubTreeFileSystem(str(data_path), fs.LocalFileSystem())

    if show_config:
        rich.print("Configuration", config.configuration)
        rich.print("Filesystem", config.filesystem)


main.add_command(config.commands)
main.add_command(obsidian.commands)

if __name__ == "__main__":
    main()
