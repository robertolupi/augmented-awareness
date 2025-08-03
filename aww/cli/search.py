import click
import lancedb
from pathlib import Path
from lancedb.embeddings import get_registry
import rich

from aww.cli import main


@main.command()
@click.argument("query")
@click.option("--rag", is_flag=True, default=False, help="Use RAG for searching.")
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
@click.pass_context
def search(ctx, query, rag, embedding_model_provider, embedding_model_name):
    """Searches the RAG index."""
    settings = ctx.obj["settings"]
    db_path = Path(settings.data_path) / "index"
    db = lancedb.connect(db_path)
    tbl = db.open_table("pages")

    if rag:
        model = (
            get_registry()
            .get(embedding_model_provider)
            .create(name=embedding_model_name)
        )
        query_vector = model.generate_embeddings([query])[0]
        results = tbl.search(query_vector).limit(10).to_df()
    else:
        results = tbl.search(query).limit(10).to_df()

    rich.print(results)
