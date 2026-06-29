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


def top_journals(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    rows = conn.execute(
        """
        SELECT journals.name, COUNT(*) AS papers, AVG(papers_t.cited_by_count) AS avg_citations
        FROM papers AS papers_t
        JOIN journals ON journals.id = papers_t.journal_id
        WHERE papers_t.project_id = ?
        GROUP BY journals.id
        ORDER BY papers DESC
        LIMIT ?
        """,
        (project_id, limit),
    ).fetchall()

    journals = [
        {
            "journal": r["name"],
            "papers": r["papers"],
            "avg_citations": round(r["avg_citations"] or 0, 2),
        }
        for r in rows
    ]

    # Bradford's Law zones: zone 1 = journals contributing ~1/3 of total papers.
    total_papers = sum(j["papers"] for j in journals)
    bradford_zones: list[str] = []
    running = 0
    zone = 1
    for j in journals:
        running += j["papers"]
        bradford_zones.append(f"Zone {zone}")
        if total_papers and running >= total_papers * (zone / 3):
            zone = min(zone + 1, 3)

    for j, z in zip(journals, bradford_zones):
        j["bradford_zone"] = z

    return {"journals": journals}


def core_journals(conn: sqlite3.Connection, project_id: int) -> dict:
    """Bradford's Law 'core' (Zone 1) journals -- the small set responsible
    for roughly a third of the corpus's output."""
    all_journals = top_journals(conn, project_id, limit=10_000)["journals"]
    return {"core": [j for j in all_journals if j["bradford_zone"] == "Zone 1"]}


def citation_impact(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT journals.name AS journal, papers.cited_by_count AS citations
        FROM papers JOIN journals ON journals.id = papers.journal_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()
    by_journal: dict[str, list[int]] = {}
    for r in rows:
        by_journal.setdefault(r["journal"], []).append(r["citations"] or 0)

    impact = {}
    for journal, counts in by_journal.items():
        impact[journal] = {
            "papers": len(counts),
            "total_citations": sum(counts),
            "avg_citations": round(sum(counts) / len(counts), 2),
            "h_index": _h_index(counts),
        }
    return impact


def journal_growth(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT papers.year AS year, journals.name AS journal, COUNT(*) AS count
        FROM papers JOIN journals ON journals.id = papers.journal_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY papers.year, journals.id ORDER BY papers.year
        """,
        (project_id,),
    ).fetchall()
    pivot: dict[str, dict[str, int]] = {}
    for r in rows:
        pivot.setdefault(str(r["year"]), {})[r["journal"]] = r["count"]
    return pivot


def journal_timeline(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT journals.name AS journal, MIN(papers.year) AS first_year, MAX(papers.year) AS last_year
        FROM papers JOIN journals ON journals.id = papers.journal_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY journals.id
        """,
        (project_id,),
    ).fetchall()
    return {
        r["journal"]: {
            "first_year": r["first_year"],
            "last_year": r["last_year"],
            "lifespan_years": r["last_year"] - r["first_year"] + 1,
        }
        for r in rows
    }


def open_access_journals(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT journals.name AS journal, COUNT(*) AS total,
               SUM(CASE WHEN papers.open_access = 1 THEN 1 ELSE 0 END) AS open_count
        FROM papers JOIN journals ON journals.id = papers.journal_id
        WHERE papers.project_id = ? GROUP BY journals.id
        """,
        (project_id,),
    ).fetchall()
    return {
        r["journal"]: {
            "total": r["total"],
            "open_pct": round(100 * (r["open_count"] or 0) / r["total"], 1) if r["total"] else 0.0,
        }
        for r in rows
    }


def publisher_distribution(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT journals.name AS journal, publishers.name AS publisher
        FROM papers
        JOIN journals ON journals.id = papers.journal_id
        LEFT JOIN publishers ON publishers.id = papers.publisher_id
        WHERE papers.project_id = ? GROUP BY journals.id
        """,
        (project_id,),
    ).fetchall()
    return {r["journal"]: r["publisher"] or "Unknown" for r in rows}
