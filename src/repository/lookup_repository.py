import sqlite3


class LookupRepository:
    """Generic get-or-create repository for simple name-keyed lookup tables
    (authors, journals, institutions, countries, publishers, keywords)."""

    def __init__(self, conn: sqlite3.Connection, table: str, name_column: str = "name"):
        self.conn = conn
        self.table = table
        self.name_column = name_column

    def get_or_create(self, name: str, **extra_columns) -> int:
        name = name.strip()
        row = self.conn.execute(
            f"SELECT id FROM {self.table} WHERE {self.name_column} = ?", (name,)
        ).fetchone()
        if row:
            return row["id"]

        columns = [self.name_column, *extra_columns.keys()]
        placeholders = ", ".join("?" for _ in columns)
        values = [name, *extra_columns.values()]
        cur = self.conn.execute(
            f"INSERT INTO {self.table} ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        return cur.lastrowid

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(f"SELECT * FROM {self.table}").fetchall()

    def get_by_id(self, entity_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            f"SELECT * FROM {self.table} WHERE id = ?", (entity_id,)
        ).fetchone()
