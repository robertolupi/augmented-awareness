import shutil
from pathlib import Path
import json
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry, EmbeddingFunctionConfig

def get_embedding_model(provider="sentence-transformers", name="all-mpnet-base-v2"):
    """Gets the embedding model from the registry."""
    return get_registry().get(provider).create(name=name)

def get_page_schema(model):
    """Creates a Pydantic model for a Page with a vector of the correct dimension."""
    class Page(LanceModel):
        id: str
        path: str
        frontmatter: str
        content: str
        vector: Vector(model.ndims())

        class Config:
            text_key = "content"
            vector_key = "vector"
    return Page

class Index:
    """Encapsulates the LanceDB index."""
    def __init__(self, db_path, embedding_model_provider="sentence-transformers", embedding_model_name="all-mpnet-base-v2"):
        self.db_path = Path(db_path)
        self.embedding_model_provider = embedding_model_provider
        self.embedding_model_name = embedding_model_name
        self.db = lancedb.connect(self.db_path)
        self.model = None
        self.Page = None
        self.tbl = None

    def _initialize_model_and_schema(self):
        if self.model is None:
            self.model = get_embedding_model(self.embedding_model_provider, self.embedding_model_name)
        if self.Page is None:
            self.Page = get_page_schema(self.model)

    def create_table(self, clean=False):
        """Creates the table for the index."""
        self._initialize_model_and_schema()
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
        self.tbl = self.db.open_table("pages")

    def add_pages(self, vault):
        """Adds pages from the vault to the index."""
        if not self.tbl:
            raise ValueError("Table not created or opened yet.")

        print("Adding pages...")
        pages_to_add = []
        for page in vault.walk():
            if page.path.is_dir():
                continue
            try:
                pages_to_add.append(
                    {
                        "id": page.name,
                        "path": str(page.path),
                        "frontmatter": json.dumps(page.frontmatter(), default=str),
                        "content": page.content(),
                    }
                )
            except TypeError as e:
                print(f"Error processing {page.path}: {e}")

        if pages_to_add:
            self.tbl.add(pages_to_add)
        return len(pages_to_add)

    def create_fts_index(self):
        """Creates the FTS index."""
        if not self.tbl:
            raise ValueError("Table not created or opened yet.")
        print("Creating FTS index...")
        self.tbl.create_fts_index("content")

    def create_vector_index(self):
        """Creates the vector index."""
        if not self.tbl:
            raise ValueError("Table not created or opened yet.")
        print("Creating RAG index...")
        self.tbl.create_index(
            metric="cosine",
            vector_column_name="vector",
            index_type="IVF_HNSW_SQ",
        )

    def search(self, query, rag=False):
        """Searches the index."""
        if not self.tbl:
            raise ValueError("Table not opened yet.")
        
        if rag:
            self._initialize_model_and_schema()
            query_vector = self.model.generate_embeddings([query])[0]
            return self.tbl.search(query_vector).limit(10).to_df()
        else:
            return self.tbl.search(query).limit(10).to_df()