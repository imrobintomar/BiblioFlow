import sqlite3


def top_keywords(conn: sqlite3.Connection, project_id: int, limit: int = 30) -> dict:
    rows = conn.execute(
        """
        SELECT keywords.term, COUNT(DISTINCT papers.id) AS papers
        FROM paper_keywords
        JOIN keywords ON keywords.id = paper_keywords.keyword_id
        JOIN papers ON papers.id = paper_keywords.paper_id
        WHERE papers.project_id = ?
        GROUP BY keywords.id
        ORDER BY papers DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    return {
        "keywords": [{"keyword": r["term"], "papers": r["papers"]} for r in rows],
        "note": "Author keywords require Scopus Abstract Retrieval (institutional access), "
        "not available with the current Search-API-only key.",
    }
