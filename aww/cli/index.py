import click
from pathlib import Path
from aww.cli import main
from aww.rag import Index


@main.command()
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help="Start from a clean state by deleting the existing index.",
)
@click.option(
    "--incr",
    is_flag=True,
    default=False,
    help="Incrementally update the index with new and modified pages.",
)
@click.pass_context
def index(ctx, clean, incr):
    """Indexes the vault for RAG."""
    settings = ctx.obj["settings"]
    vault = ctx.obj["vault"]

    idx = Index.from_settings(settings)

    since_mtime_ns = None
    if incr and not clean:
        idx.open_table()
        if idx.tbl is not None:
            since_mtime_ns = idx.get_max_mtime_ns()
            print(f"Scanning for files modified since {since_mtime_ns} ns...")
        else:
            print("No existing index found, performing a full index.")
            idx.create_table(clean=True)  # Treat as clean build
    else:
        idx.create_table(clean=clean)

    if idx.tbl is None:
        print("Failed to create or open the table. Aborting.")
        return

    num_pages = idx.add_pages(vault, since_mtime_ns=since_mtime_ns)

    if num_pages > 0:
        # Re-create indices if we've added anything
        idx.create_fts_index(replace=incr)
        idx.create_scalar_index(replace=incr)
        idx.create_vector_index(replace=incr)
        print(f"Indexed {num_pages} pages")
    if not num_pages:
        print("No new or modified pages to index.")
