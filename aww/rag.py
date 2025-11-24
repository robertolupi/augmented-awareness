import shutil
from pathlib import Path
import json
import lancedb
import pandas as pd
from lancedb.pydantic import LanceModel, Vector
from lancedb import DBConnection
from lancedb.embeddings import get_registry, EmbeddingFunctionConfig, EmbeddingFunction
from lancedb.rerankers import CrossEncoderReranker
from lancedb.table import Table

from aww.config import Settings


def get_page_schema(model) -> LanceModel:
    """Creates a Pydantic model for a Page with a vector of the correct dimension."""

    class Page(LanceModel):
        id: str
        path: str
        mtime_ns: int
        frontmatter: str
        text: str
        vector: Vector(model.ndims())

        class Config:
            text_key = "text"
            vector_key = "vector"

    return Page


class Index:
    """Encapsulates the LanceDB index."""

    db_path: Path
    embedding_model_provider: str
    embedding_model_name: str
    db: DBConnection
    model: EmbeddingFunction
    tbl: Table | None

    @classmethod
    def from_settings(cls, settings: Settings) -> "Index":
        return cls(settings.data_path, settings.rag.provider, settings.rag.model_name)

    def __init__(
        self,
        data_path: Path | str,
        embedding_model_provider: str = "sentence-transformers",
        embedding_model_name: str = "all-mpnet-base-v2",
    ):
        self.db_path = Path(data_path) / "index"
        self.embedding_model_provider = embedding_model_provider
        self.embedding_model_name = embedding_model_name
        self.db = lancedb.connect(self.db_path)
        self.model = (
            get_registry()
            .get(self.embedding_model_provider)
            .create(name=self.embedding_model_name)
        )
        self.Page = get_page_schema(self.model)
        self.tbl = None

    def create_table(self, clean=False):
        """Creates the table for the index."""
        if clean and self.db_path.exists():
            print("Removing old database...")
            shutil.rmtree(self.db_path)
            print(f"Removed existing index at {self.db_path}")

        self.tbl = self.db.create_table(
            "pages",
            schema=self.Page,
            mode="overwrite",
            embedding_functions=[
                EmbeddingFunctionConfig(
                    vector_column="vector",
                    source_column="text",
                    function=self.model,
                )
            ],
        )

    def open_table(self):
        """Opens the index table."""
        try:
            self.tbl = self.db.open_table("pages")
        except FileNotFoundError:
            self.tbl = None

    def add_pages(self, vault, since_mtime_ns: int | None = None):
        """Adds or updates pages from the vault to the index."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")

        print("Adding/updating pages...")
        pages_to_process = []
        for page in vault.walk():
            if page.path.is_dir():
                continue

            if not since_mtime_ns or page.mtime_ns() > since_mtime_ns:
                try:
                    pages_to_process.append(
                        {
                            "id": page.name,
                            "path": str(page.path),
                            "mtime_ns": page.mtime_ns(),
                            "frontmatter": json.dumps(page.frontmatter(), default=str),
                            "text": page.content(),
                        }
                    )
                except (TypeError, FileNotFoundError) as e:
                    print(f"Error processing {page.path}: {e}")

        if pages_to_process:
            ids_to_update = [p["id"] for p in pages_to_process]
            if since_mtime_ns and ids_to_update:
                ids_str = ", ".join([f"'{_id}'" for _id in ids_to_update])
                try:
                    self.tbl.delete(f"id IN ({ids_str})")
                except Exception as e:
                    print(
                        f"Could not delete old entries for updating, may result in duplicates: {e}"
                    )

            self.tbl.add(pages_to_process)
        return len(pages_to_process)

    def get_max_mtime_ns(self) -> int | None:
        """Gets the maximum mtime_ns from the index."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")

        if self.tbl.count_rows() == 0:
            return 0

        df = self.tbl.to_pandas()
        return df["mtime_ns"].max()

    def create_fts_index(self, replace: bool = False):
        """Creates the FTS index."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")
        print("Creating FTS index...")
        self.tbl.create_fts_index("text", replace=replace)

    def create_scalar_index(self, replace: bool = False):
        """Creates a scalar index on mtime_ns."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")
        print("Creating scalar index on mtime_ns...")
        self.tbl.create_scalar_index("mtime_ns", replace=replace)

    def create_vector_index(self, replace: bool = False):
        """Creates the vector index."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")
        print("Creating RAG index...")
        self.tbl.create_index(
            metric="cosine",
            vector_column_name="vector",
            index_type="IVF_HNSW_SQ",
            replace=replace,
        )

    def search(self, query, rag=False) -> pd.DataFrame:
        """Searches the index."""
        if self.tbl is None:
            raise ValueError("Table not opened yet.")

        if rag:
            query_vector = self.model.generate_embeddings([query])[0]
            results = self.tbl.search(query_vector)
        else:
            results = self.tbl.search(query, query_type="fts")
        results = results.limit(20)
        reranker = CrossEncoderReranker()
        if rag:
            results = results.rerank(reranker, query_string=query).limit(10)
        else:
            results = results.rerank(reranker).limit(10)
        return results.to_pandas()
