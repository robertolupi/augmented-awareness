import click

from aww import config

settings = config.Settings()

@click.command()
def main():
    global settings
    print(settings.model_dump())


if __name__ == "__main__":
    main()
