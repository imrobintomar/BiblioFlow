import sqlite3


class ProjectRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_or_create_default(self, pdf_dir: str) -> int:
        row = self.conn.execute("SELECT id FROM projects WHERE name = ?", ("Default",)).fetchone()
        if row:
            return row["id"]
        cur = self.conn.execute(
            "INSERT INTO projects (name, pdf_dir) VALUES (?, ?)", ("Default", pdf_dir)
        )
        return cur.lastrowid

    def list_projects(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT p.*, COUNT(papers.id) AS paper_count
            FROM projects p
            LEFT JOIN papers ON papers.project_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            """
        ).fetchall()

    def get(self, project_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    def create(self, name: str, pdf_dir: str | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO projects (name, pdf_dir) VALUES (?, ?)", (name, pdf_dir)
        )
        return cur.lastrowid

    def rename(self, project_id: int, new_name: str) -> None:
        self.conn.execute("UPDATE projects SET name = ? WHERE id = ?", (new_name, project_id))

    def delete(self, project_id: int) -> None:
        self.conn.execute("DELETE FROM papers WHERE project_id = ?", (project_id,))
        self.conn.execute("DELETE FROM events WHERE project_id = ?", (project_id,))
        self.conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
        self.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
