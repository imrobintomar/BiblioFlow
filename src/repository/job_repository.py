import sqlite3


class JobRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, project_id: int, job_type: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO jobs (project_id, type, status, started_at) "
            "VALUES (?, ?, 'running', datetime('now'))",
            (project_id, job_type),
        )
        return cur.lastrowid

    def update_progress(self, job_id: int, progress: float, message: str = "") -> None:
        self.conn.execute(
            "UPDATE jobs SET progress = ?, message = ? WHERE id = ?",
            (progress, message, job_id),
        )
        self.conn.commit()

    def finish(self, job_id: int, status: str, message: str = "") -> None:
        self.conn.execute(
            "UPDATE jobs SET status = ?, message = ?, progress = 1.0, "
            "finished_at = datetime('now') WHERE id = ?",
            (status, message, job_id),
        )
        self.conn.commit()

    def get(self, job_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
