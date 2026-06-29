import sqlite3


def most_cited_references(conn: sqlite3.Connection, project_id: int, limit: int = 20) -> dict:
    rows = conn.execute(
        """
        SELECT reference_entries.doi, COUNT(*) AS times_cited
        FROM paper_references
        JOIN reference_entries ON reference_entries.id = paper_references.reference_id
        JOIN papers ON papers.id = paper_references.paper_id
        WHERE papers.project_id = ?
        GROUP BY reference_entries.id
        ORDER BY times_cited DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    return {
        "references": [{"doi": r["doi"], "times_cited": r["times_cited"]} for r in rows],
        "note": "Reference lists require Scopus Abstract Retrieval (FULL/REF view) or "
        "CrossRef's optional reference field, neither captured yet.",
    }
