import click

from aww import config

@click.command()
def main():
    settings = config.Settings()
    print(settings.model_dump())
    print("Journal path", settings.journal_path)


if __name__ == "__main__":
    main()
