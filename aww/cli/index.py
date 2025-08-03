import click
import lancedb
from pathlib import Path
import json
import shutil
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry, EmbeddingFunctionConfig

from aww.cli import main


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

    if clean and db_path.exists():
        print("Removing old database...")
        shutil.rmtree(db_path)
        print(f"Removed existing index at {db_path}")

    db = lancedb.connect(db_path)

    model = (
        get_registry().get(embedding_model_provider).create(name=embedding_model_name)
    )

    class Page(LanceModel):
        id: str
        path: str
        frontmatter: str
        content: str
        vector: Vector(model.ndims())

        class Config:
            text_key = "content"
            vector_key = "vector"

    tbl = db.create_table(
        "pages",
        schema=Page,
        mode="overwrite",
        embedding_functions=[
            EmbeddingFunctionConfig(
                vector_column="vector",
                source_column="content",
                function=model,
            )
        ],
    )

    print("Adding pages...")

    pages = []
    for page in vault.walk():
        if page.path.is_dir():
            continue
        try:
            pages.append(
                {
                    "id": page.name,
                    "path": str(page.path),
                    "frontmatter": json.dumps(page.frontmatter(), default=str),
                    "content": page.content(),
                }
            )
        except TypeError as e:
            print(f"Error processing {page.path}: {e}")

    if pages:
        tbl.add(pages)

    print(f"Found {len(pages)} pages. Creating FTS index...")
    tbl.create_fts_index("content")
    # Create a vector index for semantic (RAG) search (HNSW)
    print(f"Creating RAG index...")
    tbl.create_index(
        metric="cosine",
        vector_column_name="vector",
        index_type="IVF_HNSW_SQ",
    )

    print(f"Indexed {len(pages)} pages in {db_path}")
