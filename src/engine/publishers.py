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


def top_publishers(conn: sqlite3.Connection, project_id: int, limit: int = 20) -> dict:
    rows = conn.execute(
        """
        SELECT publishers.name, COUNT(*) AS papers
        FROM papers JOIN publishers ON publishers.id = papers.publisher_id
        WHERE papers.project_id = ? GROUP BY publishers.id ORDER BY papers DESC LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()
    return {"publishers": [{"publisher": r["name"], "papers": r["papers"]} for r in rows]}


def publisher_growth(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT papers.year AS year, publishers.name AS publisher, COUNT(*) AS count
        FROM papers JOIN publishers ON publishers.id = papers.publisher_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY papers.year, publishers.id ORDER BY papers.year
        """,
        (project_id,),
    ).fetchall()
    pivot: dict[str, dict[str, int]] = {}
    for r in rows:
        pivot.setdefault(str(r["year"]), {})[r["publisher"]] = r["count"]
    return pivot


def citation_impact(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT publishers.name AS publisher, papers.cited_by_count AS citations
        FROM papers JOIN publishers ON publishers.id = papers.publisher_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()
    by_publisher: dict[str, list[int]] = {}
    for r in rows:
        by_publisher.setdefault(r["publisher"], []).append(r["citations"] or 0)

    impact = {}
    for publisher, counts in by_publisher.items():
        impact[publisher] = {
            "papers": len(counts),
            "total_citations": sum(counts),
            "avg_citations": round(sum(counts) / len(counts), 2),
            "h_index": _h_index(counts),
        }
    return impact


def publisher_timeline(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT publishers.name AS publisher, MIN(papers.year) AS first_year, MAX(papers.year) AS last_year
        FROM papers JOIN publishers ON publishers.id = papers.publisher_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY publishers.id
        """,
        (project_id,),
    ).fetchall()
    return {r["publisher"]: {"first_year": r["first_year"], "last_year": r["last_year"]} for r in rows}


def open_access_by_publisher(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT publishers.name AS publisher, COUNT(*) AS total,
               SUM(CASE WHEN papers.open_access = 1 THEN 1 ELSE 0 END) AS open_count
        FROM papers JOIN publishers ON publishers.id = papers.publisher_id
        WHERE papers.project_id = ? GROUP BY publishers.id
        """,
        (project_id,),
    ).fetchall()
    return {
        r["publisher"]: {
            "total": r["total"],
            "open_pct": round(100 * (r["open_count"] or 0) / r["total"], 1) if r["total"] else 0.0,
        }
        for r in rows
    }
