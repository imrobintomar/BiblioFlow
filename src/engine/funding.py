import sqlite3


def top_funders(conn: sqlite3.Connection, project_id: int, limit: int = 20) -> dict:
    rows = conn.execute(
        """
        SELECT funders.name, COUNT(DISTINCT papers.id) AS papers
        FROM paper_funders
        JOIN funders ON funders.id = paper_funders.funder_id
        JOIN papers ON papers.id = paper_funders.paper_id
        WHERE papers.project_id = ?
        GROUP BY funders.id
        ORDER BY papers DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    return {
        "funders": [{"funder": r["name"], "papers": r["papers"]} for r in rows],
        "note": "Funder names matched via a known-funder dictionary scan over the "
        "PDF's funding/acknowledgments text -- may miss funders not in the "
        "dictionary, and can false-positive when no funding section is "
        "detected and the scan falls back to full-text.",
    }
