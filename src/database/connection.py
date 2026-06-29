import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

_local = threading.local()


def init_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_connection(db_path: Path):
    """Yields a sqlite3 connection with foreign keys + Row factory enabled.

    One connection per thread (sqlite3 connections aren't thread-safe to share),
    reused across calls within the same thread to avoid reopening constantly.
    """
    if not getattr(_local, "conn", None) or getattr(_local, "db_path", None) != db_path:
        init_db(db_path)
        _local.conn = sqlite3.connect(db_path, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA foreign_keys = ON")
        _local.db_path = db_path

    conn = _local.conn
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
