import sqlite3


def language_distribution(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        "SELECT COALESCE(language, 'Unknown') AS lang, COUNT(*) AS c FROM papers "
        "WHERE project_id = ? GROUP BY lang",
        (project_id,),
    ).fetchall()
    return {"distribution": {r["lang"]: r["c"] for r in rows}}


def growth_by_language(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT year, COALESCE(language, 'Unknown') AS lang, COUNT(*) AS count FROM papers
        WHERE project_id = ? AND year IS NOT NULL
        GROUP BY year, lang ORDER BY year
        """,
        (project_id,),
    ).fetchall()
    pivot: dict[str, dict[str, int]] = {}
    for r in rows:
        pivot.setdefault(str(r["year"]), {})[r["lang"]] = r["count"]
    return pivot


def citations_by_language(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT COALESCE(language, 'Unknown') AS lang,
               COUNT(*) AS papers,
               SUM(COALESCE(cited_by_count, 0)) AS total_citations,
               AVG(cited_by_count) AS avg_citations
        FROM papers WHERE project_id = ? GROUP BY lang
        """,
        (project_id,),
    ).fetchall()
    return {
        r["lang"]: {
            "papers": r["papers"],
            "total_citations": r["total_citations"] or 0,
            "avg_citations": round(r["avg_citations"], 2) if r["avg_citations"] else 0.0,
        }
        for r in rows
    }


def journals_by_language(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT COALESCE(papers.language, 'Unknown') AS lang, COUNT(DISTINCT papers.journal_id) AS journals
        FROM papers WHERE papers.project_id = ? AND papers.journal_id IS NOT NULL
        GROUP BY lang
        """,
        (project_id,),
    ).fetchall()
    return {r["lang"]: r["journals"] for r in rows}


def country_vs_language(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT countries.name AS country, COALESCE(papers.language, 'Unknown') AS lang,
               COUNT(DISTINCT papers.id) AS count
        FROM papers
        JOIN paper_institutions ON paper_institutions.paper_id = papers.id
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN countries ON countries.id = institutions.country_id
        WHERE papers.project_id = ?
        GROUP BY countries.id, lang
        """,
        (project_id,),
    ).fetchall()
    pivot: dict[str, dict[str, int]] = {}
    for r in rows:
        pivot.setdefault(r["country"], {})[r["lang"]] = r["count"]
    return pivot
