import sqlite3
import pytest
from aww import database

@pytest.fixture
def db_conn():
    """Returns a persistent in-memory database connection."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

@pytest.fixture
def init_db_conn(db_conn):
    """Initializes the in-memory database schema."""
    database.init_db(db_conn)
    return db_conn

def test_init_db(db_conn):
    database.init_db(db_conn)
    # Check if tables exist
    cursor = db_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "tags" in tables
    assert "pages" in tables
    assert "tag_occurrences" in tables

def test_save_page_tags(init_db_conn):
    conn = init_db_conn
    source_date = "2026-01-01"
    kind = "journal"
    level = "daily"
    path = "/path/to/note.md"
    tags = ["python", "testing"]

    database.save_page_tags(conn, source_date, kind, level, path, None, None, tags)

    # Verify page
    page = conn.execute("SELECT id, source_date, path FROM pages").fetchone()
    assert page is not None
    assert page[1] == source_date
    assert page[2] == path
    page_id = page[0]

    # Verify tags
    db_tags = {row[0] for row in conn.execute("SELECT name FROM tags").fetchall()}
    assert db_tags == {"python", "testing"}

    # Verify occurrences
    occurrences = conn.execute("SELECT tag_id FROM tag_occurrences WHERE page_id=?", (page_id,)).fetchall()
    assert len(occurrences) == 2

def test_save_page_tags_update(init_db_conn):
    conn = init_db_conn
    source_date = "2026-01-01"
    kind = "journal"
    level = "daily"
    path = "/path/to/note.md"
    
    # Initial save
    database.save_page_tags(conn, source_date, kind, level, path, "h1", "u1", ["t1"])
    # Update same page
    database.save_page_tags(conn, source_date, kind, level, path, "h2", "u2", ["t2"])

    pages = conn.execute("SELECT sys_prompt_hash, user_prompt_hash FROM pages").fetchall()
    assert len(pages) == 1
    assert pages[0][0] == "h2"
    assert pages[0][1] == "u2"

    # Verify tags updated (t1 should be gone if cleared, or at least t2 present)
    tags = {row[0] for row in conn.execute("SELECT t.name FROM tags t JOIN tag_occurrences toc ON t.id=toc.tag_id").fetchall()}
    assert tags == {"t2"} 

def test_get_tags_frequency(init_db_conn):
    conn = init_db_conn
    
    # Page 1
    database.save_page_tags(conn, "2026-01-01", "journal", "daily", "p1.md", None, None, ["tag1", "tag2"])
    # Page 2
    database.save_page_tags(conn, "2026-01-02", "journal", "daily", "p2.md", None, None, ["tag1"])
    
    # Frequency
    freq = database.get_tags_frequency(conn)
    freq_dict = dict(freq)
    assert freq_dict["tag1"] == 2
    assert freq_dict["tag2"] == 1

    # Frequency with date filter
    freq_filtered = database.get_tags_frequency(conn, start_date="2026-01-02")
    freq_filtered_dict = dict(freq_filtered)
    assert freq_filtered_dict["tag1"] == 1
    assert "tag2" not in freq_filtered_dict

def test_get_tags_references(init_db_conn):
    conn = init_db_conn
    
    database.save_page_tags(conn, "2026-01-01", "journal", "daily", "p1.md", None, None, ["tag1"])
    
    refs = database.get_tags_references(conn)
    assert len(refs) == 1
    assert refs[0][0] == "tag1"
    assert refs[0][1] == "2026-01-01"
    assert refs[0][4] == "p1.md"
