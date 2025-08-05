import shutil
from pathlib import Path
import json
import lancedb
import pandas as pd
from lancedb.pydantic import LanceModel, Vector
from lancedb import DBConnection
from lancedb.embeddings import get_registry, EmbeddingFunctionConfig, EmbeddingFunction
from lancedb.table import Table


def get_page_schema(model) -> LanceModel:
    """Creates a Pydantic model for a Page with a vector of the correct dimension."""

    class Page(LanceModel):
        id: str
        path: str
        mtime_ns: int
        frontmatter: str
        content: str
        vector: Vector(model.ndims())

        class Config:
            text_key = "content"
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

    def __init__(
        self,
        db_path,
        embedding_model_provider="sentence-transformers",
        embedding_model_name="all-mpnet-base-v2",
    ):
        self.db_path = Path(db_path)
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
                    source_column="content",
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
                            "frontmatter": json.dumps(
                                page.frontmatter(), default=str
                            ),
                            "content": page.content(),
                        }
                    )
                except (TypeError, FileNotFoundError) as e:
                    print(f"Error processing {page.path}: {e}")

        if pages_to_process:
            ids_to_update = [p["id"] for p in pages_to_process]
            if since_mtime_ns and ids_to_update:
                ids_str = ", ".join([f"'{_id}'" for _id in ids_to_update])
                try:
                    self.tbl.delete(f'id IN ({ids_str})')
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

        try:
            # This is efficient if there's a scalar index on mtime_ns
            df = (
                self.tbl.search()
                .select(["mtime_ns"])
                .limit(1)
                .sort_by("mtime_ns", ascending=False)
                .to_df()
            )
            if not df.empty:
                return int(df["mtime_ns"][0])
        except Exception:
            # Fallback for when sorting isn't supported (e.g., no index)
            all_mtime = self.tbl.to_pandas(columns=["mtime_ns"])
            if not all_mtime.empty:
                return int(all_mtime["mtime_ns"].max())
        return 0

    def create_fts_index(self):
        """Creates the FTS index."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")
        print("Creating FTS index...")
        self.tbl.create_fts_index("content")

    def create_scalar_index(self):
        """Creates a scalar index on mtime_ns."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")
        print("Creating scalar index on mtime_ns...")
        self.tbl.create_index("mtime_ns")

    def create_vector_index(self):
        """Creates the vector index."""
        if self.tbl is None:
            raise ValueError("Table not created or opened yet.")
        print("Creating RAG index...")
        self.tbl.create_index(
            metric="cosine",
            vector_column_name="vector",
            index_type="IVF_HNSW_SQ",
        )

    def search(self, query, rag=False) -> pd.DataFrame:
        """Searches the index."""
        if self.tbl is None:
            raise ValueError("Table not opened yet.")

        if rag:
            query_vector = self.model.generate_embeddings([query])[0]
            return self.tbl.search(query_vector).limit(10).to_df()
        else:
            return self.tbl.search(query).limit(10).to_df()
