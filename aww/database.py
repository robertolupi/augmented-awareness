import sqlite3
from pathlib import Path


def get_db_path(settings):
    """Return the path to the SQLite database, creating the directory if needed."""
    data_path = Path(settings.data_path).expanduser()
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path / "aww.db"


def init_db(db_path_or_conn):
    """Initialize the database schema."""
    if isinstance(db_path_or_conn, sqlite3.Connection):
        conn = db_path_or_conn
        _init_db(conn)
    else:
        with sqlite3.connect(db_path_or_conn) as conn:
            _init_db(conn)


def _init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_date TEXT NOT NULL,
            kind TEXT NOT NULL,
            level TEXT NOT NULL,
            path TEXT NOT NULL,
            sys_prompt_hash TEXT,
            user_prompt_hash TEXT,
            UNIQUE(source_date, kind, level, path)
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tag_occurrences (
            tag_id INTEGER REFERENCES tags(id),
            page_id INTEGER REFERENCES pages(id),
            PRIMARY KEY (tag_id, page_id)
        )
    """
    )


def save_page_tags(
    db_path_or_conn, source_date, kind, level, path, sys_hash, user_hash, tags
):
    """Upsert page info and its associated tags."""
    if isinstance(db_path_or_conn, sqlite3.Connection):
        _save_page_tags(
            db_path_or_conn,
            source_date,
            kind,
            level,
            path,
            sys_hash,
            user_hash,
            tags,
        )
    else:
        with sqlite3.connect(db_path_or_conn) as conn:
            _save_page_tags(
                conn, source_date, kind, level, path, sys_hash, user_hash, tags
            )


def _save_page_tags(conn, source_date, kind, level, path, sys_hash, user_hash, tags):
    # Insert or update page
    conn.execute(
        """
        INSERT INTO pages (source_date, kind, level, path, sys_prompt_hash, user_prompt_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_date, kind, level, path) DO UPDATE SET
            sys_prompt_hash=excluded.sys_prompt_hash,
            user_prompt_hash=excluded.user_prompt_hash
    """,
        (source_date, kind, level, str(path), sys_hash, user_hash),
    )

    page_id = conn.execute(
        "SELECT id FROM pages WHERE source_date=? AND kind=? AND level=? AND path=?",
        (source_date, kind, level, str(path)),
    ).fetchone()[0]

    # Clear existing occurrences for this page
    conn.execute("DELETE FROM tag_occurrences WHERE page_id = ?", (page_id,))

    for tag_name in tags:
        # Insert tag if not exists
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
        tag_id = conn.execute(
            "SELECT id FROM tags WHERE name = ?", (tag_name,)
        ).fetchone()[0]

        # Insert occurrence
        conn.execute(
            "INSERT OR IGNORE INTO tag_occurrences (tag_id, page_id) VALUES (?, ?)",
            (tag_id, page_id),
        )


def get_tags_frequency(db_path_or_conn, start_date=None, end_date=None, level=None):
    """Query tag counts in a given period and level."""
    if isinstance(db_path_or_conn, sqlite3.Connection):
        return _get_tags_frequency(
            db_path_or_conn, start_date, end_date, level
        )
    else:
        with sqlite3.connect(db_path_or_conn) as conn:
            return _get_tags_frequency(conn, start_date, end_date, level)


def _get_tags_frequency(conn, start_date=None, end_date=None, level=None):
    params = []
    where_clauses = ["1=1"]

    if start_date:
        where_clauses.append("p.source_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("p.source_date <= ?")
        params.append(end_date)
    if level:
        where_clauses.append("p.level = ?")
        params.append(level.lower())

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT t.name, COUNT(toc.page_id) as freq
        FROM tags t
        JOIN tag_occurrences toc ON t.id = toc.tag_id
        JOIN pages p ON toc.page_id = p.id
        WHERE {where_sql}
        GROUP BY t.name
        ORDER BY freq DESC, t.name ASC
    """

    return conn.execute(query, params).fetchall()


def get_tags_references(db_path_or_conn, start_date=None, end_date=None, level=None):
    """Query tag occurrences with page details in a given period and level."""
    if isinstance(db_path_or_conn, sqlite3.Connection):
        return _get_tags_references(
            db_path_or_conn, start_date, end_date, level
        )
    else:
        with sqlite3.connect(db_path_or_conn) as conn:
            return _get_tags_references(conn, start_date, end_date, level)


def _get_tags_references(conn, start_date=None, end_date=None, level=None):
    params = []
    where_clauses = ["1=1"]

    if start_date:
        where_clauses.append("p.source_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("p.source_date <= ?")
        params.append(end_date)
    if level:
        where_clauses.append("p.level = ?")
        params.append(level.lower())

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT t.name, p.source_date, p.kind, p.level, p.path
        FROM tags t
        JOIN tag_occurrences toc ON t.id = toc.tag_id
        JOIN pages p ON toc.page_id = p.id
        WHERE {where_sql}
        ORDER BY t.name ASC, p.source_date DESC
    """

    return conn.execute(query, params).fetchall()
