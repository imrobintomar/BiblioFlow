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


def top_authors(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    rows = conn.execute(
        """
        SELECT authors.full_name, papers.cited_by_count
        FROM paper_authors
        JOIN authors ON authors.id = paper_authors.author_id
        JOIN papers ON papers.id = paper_authors.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()

    by_author: dict[str, list[int]] = {}
    for r in rows:
        by_author.setdefault(r["full_name"], []).append(r["cited_by_count"] or 0)

    productivity = []
    for name, citations in by_author.items():
        productivity.append(
            {
                "author": name,
                "papers": len(citations),
                "total_citations": sum(citations),
                "avg_citations": round(sum(citations) / len(citations), 2),
                "h_index": _h_index(citations),
            }
        )

    productivity.sort(key=lambda x: (x["papers"], x["total_citations"]), reverse=True)
    return {"authors": productivity[:limit], "total_distinct_authors": len(by_author)}
