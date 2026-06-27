import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_state (
    filename TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    status TEXT NOT NULL,
    doi TEXT,
    error TEXT,
    record_json TEXT,
    updated_at TEXT NOT NULL
);
"""


@contextmanager
def get_connection(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_state(conn: sqlite3.Connection, filename: str) -> sqlite3.Row | None:
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT * FROM pipeline_state WHERE filename = ?", (filename,)
    )
    return cur.fetchone()


def upsert_state(
    conn: sqlite3.Connection,
    filename: str,
    checksum: str,
    status: str,
    doi: str | None,
    error: str | None,
    record_json: str,
) -> None:
    conn.execute(
        """
        INSERT INTO pipeline_state (filename, checksum, status, doi, error, record_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(filename) DO UPDATE SET
            checksum = excluded.checksum,
            status = excluded.status,
            doi = excluded.doi,
            error = excluded.error,
            record_json = excluded.record_json,
            updated_at = excluded.updated_at
        """,
        (filename, checksum, status, doi, error, record_json),
    )
