import sqlite3


def top_institutions(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    rows = conn.execute(
        """
        SELECT institutions.name, COUNT(DISTINCT papers.id) AS papers
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        GROUP BY institutions.id
        ORDER BY papers DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    return {"institutions": [{"institution": r["name"], "papers": r["papers"]} for r in rows]}
