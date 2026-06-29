import sqlite3


class EventRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def log(
        self,
        project_id: int | None,
        event_type: str,
        status: str,
        message: str = "",
        duration_ms: int | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO events (project_id, type, status, message, duration_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, event_type, status, message, duration_ms),
        )
        return cur.lastrowid

    def recent(self, project_id: int | None = None, limit: int = 20) -> list[sqlite3.Row]:
        if project_id is not None:
            return self.conn.execute(
                "SELECT * FROM events WHERE project_id = ? ORDER BY timestamp DESC LIMIT ?",
                (project_id, limit),
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
