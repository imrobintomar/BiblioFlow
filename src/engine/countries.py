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


def most_cited_countries(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    """Matches biblioshiny's 'Most Cited Countries' -- total citations of
    papers affiliated with each country (via institution affiliation)."""
    rows = conn.execute(
        """
        SELECT countries.name AS country, SUM(DISTINCT_PAPER.cited_by_count) AS total_citations
        FROM (
            SELECT DISTINCT paper_institutions.paper_id, institutions.country_id, papers.cited_by_count
            FROM paper_institutions
            JOIN institutions ON institutions.id = paper_institutions.institution_id
            JOIN papers ON papers.id = paper_institutions.paper_id
            WHERE papers.project_id = ? AND institutions.country_id IS NOT NULL
        ) AS DISTINCT_PAPER
        JOIN countries ON countries.id = DISTINCT_PAPER.country_id
        GROUP BY countries.id
        ORDER BY total_citations DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    return {"countries": [{"country": r["country"], "total_citations": r["total_citations"] or 0} for r in rows]}
