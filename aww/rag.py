import json
import shutil
from pathlib import Path
from typing import List, Union

from pydantic import ConfigDict
import lancedb
import numpy as np
import pandas as pd
from lancedb.pydantic import LanceModel, Vector
from lancedb import DBConnection
from lancedb.embeddings import (
    get_registry,
    EmbeddingFunctionConfig,
    EmbeddingFunction,
    TextEmbeddingFunction,
)
from lancedb.embeddings.utils import weak_lru
from lancedb.util import attempt_import_or_raise
from lancedb.rerankers import CrossEncoderReranker
from functools import cached_property
import pyarrow as pa
from lancedb.table import Table

from aww.config import Settings
from aww.huggingface import load_cross_encoder, load_sentence_transformer


def get_page_schema(model) -> LanceModel:
    """Creates a Pydantic model for a Page with a vector of the correct dimension."""

    class Page(LanceModel):
        id: str
        path: str
        mtime_ns: int
        frontmatter: str
        text: str
        vector: Vector(model.ndims())

        model_config = ConfigDict(
            text_key="text",
            vector_key="vector",
        )

    return Page


class Index:
    """Encapsulates the LanceDB index."""

    db_path: Path
    embedding_model_provider: str
    embedding_model_name: str
    local_files_only: bool
    cache_dir: str | None
    reranker_model_name: str
    db: DBConnection
    model: EmbeddingFunction | None
    tbl: Table | None

    @classmethod
    def from_settings(cls, settings: Settings) -> "Index":
        return cls(
            settings.data_path,
            settings.rag.provider,
            settings.rag.model_name,
            local_files_only=settings.rag.local_files_only,
            cache_dir=settings.rag.cache_dir,
        )

    def __init__(
        self,
        data_path: Path | str,
        embedding_model_provider: str = "sentence-transformers",
        embedding_model_name: str = "all-mpnet-base-v2",
        local_files_only: bool = True,
        cache_dir: str | None = None,
        reranker_model_name: str = "cross-encoder/ms-marco-TinyBERT-L-6",
    ):
        self.db_path = Path(data_path) / "index"
        self.embedding_model_provider = embedding_model_provider
        self.embedding_model_name = embedding_model_name
        self.local_files_only = local_files_only
        self.cache_dir = cache_dir
        self.reranker_model_name = reranker_model_name
        self.db = lancedb.connect(self.db_path)
        self.model = None
        self.Page = None
        self.tbl = None

    def _build_embedding_model(self) -> EmbeddingFunction:
        if self.embedding_model_provider == "sentence-transformers":
            return LocalSentenceTransformerEmbeddings.create(
                name=self.embedding_model_name,
                local_files_only=self.local_files_only,
                cache_folder=self.cache_dir,
                token=False,
            )
        return (
            get_registry()
            .get(self.embedding_model_provider)
            .create(name=self.embedding_model_name)
        )

    def get_model(self) -> EmbeddingFunction:
        if self.model is None:
            self.model = self._build_embedding_model()
        return self.model

    def get_page_schema(self) -> LanceModel:
        if self.Page is None:
            self.Page = get_page_schema(self.get_model())
        return self.Page

    def create_table(self, clean=False):
        """Creates the table for the index."""
        if clean and self.db_path.exists():
            print("Removing old database...")
            shutil.rmtree(self.db_path)
            print(f"Removed existing index at {self.db_path}")

        self.tbl = self.db.create_table(
            "pages",
            schema=self.get_page_schema(),
            mode="overwrite",
            embedding_functions=[
                EmbeddingFunctionConfig(
                    vector_column="vector",
                    source_column="text",
                    function=self.get_model(),
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
            query_vector = self.get_model().generate_embeddings([query])[0]
            results = self.tbl.search(query_vector)
        else:
            results = self.tbl.search(query, query_type="fts")
        results = results.limit(20)
        reranker = LocalCrossEncoderReranker(
            model_name=self.reranker_model_name,
            local_files_only=self.local_files_only,
            cache_folder=self.cache_dir,
            token=False,
        )
        if rag:
            results = results.rerank(reranker, query_string=query).limit(10)
        else:
            results = results.rerank(reranker).limit(10)
        return results.to_pandas()


class LocalSentenceTransformerEmbeddings(TextEmbeddingFunction):
    name: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    normalize: bool = True
    trust_remote_code: bool = True
    local_files_only: bool = True
    token: bool | str | None = False
    cache_folder: str | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ndims = None

    @property
    def embedding_model(self):
        return self.get_embedding_model()

    def ndims(self):
        if self._ndims is None:
            self._ndims = len(self.generate_embeddings("foo")[0])
        return self._ndims

    def generate_embeddings(
        self, texts: Union[List[str], np.ndarray]
    ) -> List[np.array]:
        embeddings = self.embedding_model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=self.normalize,
        )
        return np.asarray(embeddings).tolist()

    @weak_lru(maxsize=1)
    def get_embedding_model(self):
        attempt_import_or_raise("sentence_transformers", "sentence-transformers")
        return load_sentence_transformer(
            self.name,
            device=self.device,
            trust_remote_code=self.trust_remote_code,
            local_files_only=self.local_files_only,
            token=self.token,
            cache_folder=self.cache_folder,
        )


class LocalCrossEncoderReranker(CrossEncoderReranker):
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-TinyBERT-L-6",
        column: str = "text",
        device: str | None = None,
        return_score: str = "relevance",
        trust_remote_code: bool = True,
        local_files_only: bool = True,
        token: bool | str | None = False,
        cache_folder: str | None = None,
    ):
        super().__init__(
            model_name=model_name,
            column=column,
            device=device,
            return_score=return_score,
            trust_remote_code=trust_remote_code,
        )
        self.local_files_only = local_files_only
        self.token = token
        self.cache_folder = cache_folder

    @cached_property
    def model(self):
        attempt_import_or_raise("sentence_transformers")
        return load_cross_encoder(
            self.model_name,
            device=self.device,
            trust_remote_code=self.trust_remote_code,
            local_files_only=self.local_files_only,
            token=self.token,
            cache_folder=self.cache_folder,
        )
