import time
import pytest
from pathlib import Path
import tempfile
import shutil

from aww.rag import Index
from aww.obsidian import Vault


@pytest.fixture
def temp_db_path() -> Path:
    """Creates a temporary directory for the test database."""
    db_path = Path(tempfile.gettempdir()) / "test_aww_index"
    if db_path.exists():
        shutil.rmtree(db_path)
    db_path.mkdir()
    yield db_path
    shutil.rmtree(db_path)


@pytest.fixture
def test_vault() -> Vault:
    """Returns a Vault instance pointing to the test_vault directory."""
    # Assuming the test is run from the project root
    vault_path = Path.cwd() / "test_vault"
    return Vault(
        path=vault_path, journal_dir="journal", retrospectives_dir="retrospectives"
    )


def test_index_creation_and_full_rebuild(temp_db_path: Path, test_vault: Vault):
    """Test creating a new index and adding all pages from the vault."""
    idx = Index(db_path=temp_db_path)

    # 1. Create a clean table
    idx.create_table(clean=True)
    assert idx.tbl is not None, "Table should be created"
    assert idx.tbl.count_rows() == 0

    # 2. Add pages
    num_added = idx.add_pages(test_vault)
    assert num_added == 3  # test_vault has 3 markdown files
    assert idx.tbl.count_rows() == 3

    # 3. Create indices
    idx.create_fts_index()
    idx.create_scalar_index()
    idx.create_vector_index()

    # 4. Verify content
    df = idx.tbl.to_pandas()
    assert "index" in df["id"].values
    assert "2025-03-30" in df["id"].values
    assert "2025-04-01" in df["id"].values


def test_fts_search(temp_db_path: Path, test_vault: Vault):
    """Test full-text search functionality."""
    idx = Index(db_path=temp_db_path)
    idx.create_table(clean=True)
    idx.add_pages(test_vault)
    idx.create_fts_index()

    # Search for a term that exists in multiple documents
    results = idx.search("frontmatter")
    assert not results.empty
    assert len(results) == 3
    ids = results["id"].tolist()
    assert "index" in ids
    assert "2025-03-30" in ids
    assert "2025-04-01" in ids

    # Search for a term that only exists in one document

    results = idx.search("yoga")
    assert not results.empty
    assert len(results) == 1
    assert results["id"].iloc[0] == "2025-03-30"


def test_rag_search(temp_db_path: Path, test_vault: Vault):
    """Test vector search (RAG) functionality."""
    idx = Index(db_path=temp_db_path)
    idx.create_table(clean=True)
    idx.add_pages(test_vault)
    idx.create_vector_index()

    results = idx.search("what is yoga?", rag=True)
    assert not results.empty
    assert len(results) > 0
    # The top result should be the page mentioning yoga
    assert results["id"].iloc[0] == "2025-03-30"


def test_incremental_indexing(temp_db_path: Path, test_vault: Vault):
    """Test that incremental indexing only adds new or modified files."""
    idx = Index(db_path=temp_db_path)

    # 1. Initial full index
    idx.create_table(clean=True)
    idx.add_pages(test_vault)
    idx.create_scalar_index()
    assert idx.tbl.count_rows() == 3

    # Get the latest modification time
    max_mtime = idx.get_max_mtime_ns()
    assert max_mtime is not None and max_mtime > 0

    # Let some time pass to ensure the new mtime is greater
    time.sleep(0.01)

    # 2. Create a new file and modify an existing one
    new_file_path = test_vault.path / "new_test_file.md"
    modified_file_path = test_vault.path / "index.md"

    try:
        new_file_path.write_text("This is a new file for incremental test.")
        modified_file_path.touch()

        # 3. Run incremental update
        # Re-open the table to simulate a new run
        idx.open_table()
        num_added = idx.add_pages(test_vault, since_mtime_ns=max_mtime)

        # We expect 2 files to be processed: the new one and the modified one.
        assert num_added == 2

        # The table should now have 4 entries (3 original + 1 new, 1 updated)
        # The add_pages method with `since_mtime_ns` deletes old versions before adding.
        assert idx.tbl.count_rows() == 4

        # Verify the new file is there
        df = idx.tbl.search("new_test_file").to_pandas()
        assert not df.empty
        assert df.iloc[0]["id"] == "new_test_file"

    finally:
        # 4. Clean up the created file
        if new_file_path.exists():
            new_file_path.unlink()
