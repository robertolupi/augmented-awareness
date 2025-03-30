import click
import rich
import rich.table

from aww.observe.obsidian import Vault

vault: Vault


@click.group()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
def main(vault_path):
    global vault
    vault = Vault(vault_path)


@main.command()
@click.option('verbose', '-v', is_flag=True, help='Verbose output. Print markdown content.')
@click.argument('page_name', type=str, required=False)
def info(verbose, page_name=None):
    global vault
    rich.print(vault.path)
    pages = vault.pages()
    journal = vault.journal()

    rich.print(f"Total Pages: {len(pages)}")
    rich.print(f"Journal pages: {len(journal)}")
    if not page_name:
        entry = list(journal.values())[-1]
    else:
        entry = pages.get(page_name)
    if not entry:
        rich.print("[bold red]Page not found[/bold red]")
        return
    rich.print("\n")
    rich.print(f"Page: {entry.name}")
    rich.print(f"Frontmatter: {entry.frontmatter()}")
    rich.print(f"Tags: {entry.tags()}")
    if verbose:
        rich.print(entry.content())


if __name__ == "__main__":
    main()
