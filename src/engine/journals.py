import sqlite3


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
