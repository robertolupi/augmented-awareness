import click
from pathlib import Path
from aww.cli import main
from aww.rag import Index


@main.command()
@click.option(
    "--embedding-model-provider",
    type=str,
    default="sentence-transformers",
    help="The embedding model provider.",
)
@click.option(
    "--embedding-model-name",
    type=str,
    default="all-mpnet-base-v2",
    help="The embedding model name.",
)
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help="Start from a clean state by deleting the existing index.",
)
@click.pass_context
def index(ctx, embedding_model_provider, embedding_model_name, clean):
    """Indexes the vault for RAG."""
    settings = ctx.obj["settings"]
    vault = ctx.obj["vault"]
    db_path = Path(settings.data_path) / "index"

    idx = Index(db_path, embedding_model_provider, embedding_model_name)
    idx.create_table(clean=clean)
    num_pages = idx.add_pages(vault)
    if num_pages > 0:
        idx.create_fts_index()
        idx.create_vector_index()
    print(f"Indexed {num_pages} pages in {db_path}")
