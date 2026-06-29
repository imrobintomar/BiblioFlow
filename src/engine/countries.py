import sqlite3


def top_countries(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    rows = conn.execute(
        """
        SELECT countries.name, COUNT(DISTINCT papers.id) AS papers
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN countries ON countries.id = institutions.country_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        GROUP BY countries.id
        ORDER BY papers DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    return {
        "countries": [{"country": r["name"], "papers": r["papers"]} for r in rows],
        "note": "Country data requires an affiliation-to-country lookup, not yet implemented.",
    }
