import sqlite3


def _h_index(citation_counts: list[int]) -> int:
    sorted_counts = sorted(citation_counts, reverse=True)
    h = 0
    for i, c in enumerate(sorted_counts, start=1):
        if c >= i:
            h = i
        else:
            break
    return h


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


def institution_growth(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    top_names = [i["institution"] for i in top_institutions(conn, project_id, limit)["institutions"]]
    if not top_names:
        return {}
    placeholders = ",".join("?" for _ in top_names)
    rows = conn.execute(
        f"""
        SELECT papers.year AS year, institutions.name AS institution, COUNT(DISTINCT papers.id) AS count
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL AND institutions.name IN ({placeholders})
        GROUP BY papers.year, institutions.id ORDER BY papers.year
        """,
        (project_id, *top_names),
    ).fetchall()
    pivot: dict[str, dict[str, int]] = {}
    for r in rows:
        pivot.setdefault(str(r["year"]), {})[r["institution"]] = r["count"]
    return pivot


def citation_impact(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT institutions.name AS institution, papers.cited_by_count AS citations
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()
    by_institution: dict[str, list[int]] = {}
    for r in rows:
        by_institution.setdefault(r["institution"], []).append(r["citations"] or 0)

    impact = {}
    for institution, counts in by_institution.items():
        impact[institution] = {
            "papers": len(counts),
            "total_citations": sum(counts),
            "avg_citations": round(sum(counts) / len(counts), 2),
            "h_index": _h_index(counts),
        }
    return impact


def collaboration(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    """Institution co-occurrence on shared papers (the underlying edge list
    for an institution network, not yet rendered as a graph -- that's a
    future Network Analysis milestone)."""
    rows = conn.execute(
        """
        SELECT paper_institutions.paper_id AS paper_id, institutions.name AS institution
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()

    institutions_by_paper: dict[int, set[str]] = {}
    for r in rows:
        institutions_by_paper.setdefault(r["paper_id"], set()).add(r["institution"])

    co_institutions: dict[str, set[str]] = {}
    for institutions_on_paper in institutions_by_paper.values():
        for inst in institutions_on_paper:
            co_institutions.setdefault(inst, set()).update(institutions_on_paper - {inst})

    results = sorted(
        ({"institution": k, "co_institutions": len(v)} for k, v in co_institutions.items()),
        key=lambda x: x["co_institutions"],
        reverse=True,
    )
    return {"collaboration": results[:limit]}


def top_researchers(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    """Paper-level proxy: authors on any paper linked to this institution --
    not true author-to-institution attribution, since the schema links
    papers (not individual authors) to institutions."""
    rows = conn.execute(
        """
        SELECT institutions.name AS institution, authors.full_name AS author
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN paper_authors ON paper_authors.paper_id = paper_institutions.paper_id
        JOIN authors ON authors.id = paper_authors.author_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()

    by_institution: dict[str, set[str]] = {}
    for r in rows:
        by_institution.setdefault(r["institution"], set()).add(r["author"])

    results = sorted(
        ({"institution": k, "distinct_researchers": len(v)} for k, v in by_institution.items()),
        key=lambda x: x["distinct_researchers"],
        reverse=True,
    )
    return {"researchers": results[:limit]}


def publication_timeline(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT institutions.name AS institution, MIN(papers.year) AS first_year, MAX(papers.year) AS last_year
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY institutions.id
        """,
        (project_id,),
    ).fetchall()
    return {r["institution"]: {"first_year": r["first_year"], "last_year": r["last_year"]} for r in rows}


def country_distribution(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT institutions.name AS institution, countries.name AS country
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        LEFT JOIN countries ON countries.id = institutions.country_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        GROUP BY institutions.id
        """,
        (project_id,),
    ).fetchall()
    return {r["institution"]: r["country"] or "Unknown" for r in rows}


def funding_distribution(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    """Paper-level proxy: funders on any paper linked to this institution --
    the schema has no direct institution-to-funder edge."""
    rows = conn.execute(
        """
        SELECT institutions.name AS institution, funders.name AS funder
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN paper_funders ON paper_funders.paper_id = paper_institutions.paper_id
        JOIN funders ON funders.id = paper_funders.funder_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()

    by_institution: dict[str, set[str]] = {}
    for r in rows:
        by_institution.setdefault(r["institution"], set()).add(r["funder"])

    results = sorted(
        ({"institution": k, "funders": sorted(v)} for k, v in by_institution.items()),
        key=lambda x: len(x["funders"]),
        reverse=True,
    )
    return {"funding": results[:limit]}
