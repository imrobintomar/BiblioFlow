import sqlite3
from datetime import datetime


def _h_index(citation_counts: list[int]) -> int:
    sorted_counts = sorted(citation_counts, reverse=True)
    h = 0
    for i, c in enumerate(sorted_counts, start=1):
        if c >= i:
            h = i
        else:
            break
    return h


def _g_index(citation_counts: list[int]) -> int:
    sorted_counts = sorted(citation_counts, reverse=True)
    running = 0
    g = 0
    for i, c in enumerate(sorted_counts, start=1):
        running += c
        if running >= i * i:
            g = i
        else:
            break
    return g


def _i10_index(citation_counts: list[int]) -> int:
    return sum(1 for c in citation_counts if c >= 10)


def _contemporary_h_index(papers: list[dict], current_year: int) -> int:
    """Sidiropoulos et al. contemporary h-index: each paper's citation
    count is age-weighted (S_i = 4 * C_i / (age_i + 1)), then h-index is
    computed over those weighted scores instead of raw counts."""
    scores = []
    for p in papers:
        age = max(0, current_year - (p["year"] or current_year))
        scores.append(round(4 * (p["citations"] or 0) / (age + 1)))
    return _h_index(scores)


def top_authors(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    rows = conn.execute(
        """
        SELECT authors.full_name AS author, papers.id AS paper_id, papers.year AS year,
               papers.cited_by_count AS citations,
               (SELECT COUNT(*) FROM paper_authors pa2 WHERE pa2.paper_id = papers.id) AS author_count
        FROM paper_authors
        JOIN authors ON authors.id = paper_authors.author_id
        JOIN papers ON papers.id = paper_authors.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()

    by_author: dict[str, list[dict]] = {}
    for r in rows:
        by_author.setdefault(r["author"], []).append(
            {"paper_id": r["paper_id"], "year": r["year"], "citations": r["citations"] or 0, "author_count": r["author_count"]}
        )

    current_year = datetime.now().year
    profiles = []
    for name, papers in by_author.items():
        citation_counts = [p["citations"] for p in papers]
        years = [p["year"] for p in papers if p["year"]]
        first_year, last_year = (min(years), max(years)) if years else (None, None)
        active_years = (last_year - first_year + 1) if first_year and last_year else 1
        h = _h_index(citation_counts)
        total_citations = sum(citation_counts)
        fractional = sum(1 / p["author_count"] for p in papers if p["author_count"])

        profiles.append(
            {
                "author": name,
                "papers": len(papers),
                "fractional_papers": round(fractional, 2),
                "first_publication": first_year,
                "latest_publication": last_year,
                "active_years": active_years,
                "total_citations": total_citations,
                "avg_citations": round(total_citations / len(papers), 2),
                "h_index": h,
                "g_index": _g_index(citation_counts),
                "i10_index": _i10_index(citation_counts),
                "m_index": round(h / active_years, 2) if active_years else 0.0,
                "contemporary_h_index": _contemporary_h_index(papers, current_year),
                "normalized_h_index": round(h / len(papers), 2) if papers else 0.0,
                "citation_velocity": round(total_citations / active_years, 2) if active_years else 0.0,
            }
        )

    profiles.sort(key=lambda x: (x["papers"], x["total_citations"]), reverse=True)
    return {"authors": profiles[:limit], "total_distinct_authors": len(by_author)}


def productivity_timeline(conn: sqlite3.Connection, project_id: int, limit: int = 8) -> dict:
    top_names = [
        r["author"]
        for r in conn.execute(
            """
            SELECT authors.full_name AS author, COUNT(*) AS c FROM paper_authors
            JOIN authors ON authors.id = paper_authors.author_id
            JOIN papers ON papers.id = paper_authors.paper_id
            WHERE papers.project_id = ? GROUP BY authors.id ORDER BY c DESC LIMIT ?
            """,
            (project_id, limit),
        ).fetchall()
    ]
    if not top_names:
        return {}

    placeholders = ",".join("?" for _ in top_names)
    rows = conn.execute(
        f"""
        SELECT papers.year AS year, authors.full_name AS author, COUNT(*) AS count
        FROM paper_authors
        JOIN authors ON authors.id = paper_authors.author_id
        JOIN papers ON papers.id = paper_authors.paper_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL AND authors.full_name IN ({placeholders})
        GROUP BY papers.year, authors.id ORDER BY papers.year
        """,
        (project_id, *top_names),
    ).fetchall()

    pivot: dict[str, dict[str, int]] = {}
    for r in rows:
        pivot.setdefault(str(r["year"]), {})[r["author"]] = r["count"]
    return pivot


def collaboration_stats(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    """Co-author counts are exact (from paper_authors). Institution/country
    collaboration are paper-level proxies, not true per-author attribution
    -- the schema links papers to institutions, not individual authors to
    their specific institution, so an author's own collaboration footprint
    can't be isolated from their co-authors' on a shared paper."""
    rows = conn.execute(
        """
        SELECT authors.full_name AS author, paper_authors.paper_id AS paper_id
        FROM paper_authors
        JOIN authors ON authors.id = paper_authors.author_id
        JOIN papers ON papers.id = paper_authors.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()

    papers_by_author: dict[str, set[int]] = {}
    for r in rows:
        papers_by_author.setdefault(r["author"], set()).add(r["paper_id"])

    coauthors_by_paper: dict[int, set[str]] = {}
    for r in rows:
        coauthors_by_paper.setdefault(r["paper_id"], set()).add(r["author"])

    countries_by_paper: dict[int, set[str]] = {}
    for r in conn.execute(
        """
        SELECT paper_institutions.paper_id AS paper_id, countries.name AS country
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN countries ON countries.id = institutions.country_id
        """
    ).fetchall():
        countries_by_paper.setdefault(r["paper_id"], set()).add(r["country"])

    results = []
    for author, paper_ids in papers_by_author.items():
        co_authors = set()
        countries = set()
        international_papers = 0
        for pid in paper_ids:
            co_authors |= coauthors_by_paper.get(pid, set()) - {author}
            paper_countries = countries_by_paper.get(pid, set())
            countries |= paper_countries
            if len(paper_countries) > 1:
                international_papers += 1

        results.append(
            {
                "author": author,
                "distinct_co_authors": len(co_authors),
                "distinct_countries_touched": len(countries),
                "international_papers": international_papers,
                "domestic_papers": len(paper_ids) - international_papers,
            }
        )

    results.sort(key=lambda x: x["distinct_co_authors"], reverse=True)
    return {"collaboration": results[:limit]}


def career_stats(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    rows = conn.execute(
        """
        SELECT authors.full_name AS author, papers.year AS year, papers.cited_by_count AS citations
        FROM paper_authors
        JOIN authors ON authors.id = paper_authors.author_id
        JOIN papers ON papers.id = paper_authors.paper_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        """,
        (project_id,),
    ).fetchall()

    by_author: dict[str, list[dict]] = {}
    for r in rows:
        by_author.setdefault(r["author"], []).append({"year": r["year"], "citations": r["citations"] or 0})

    results = []
    for author, papers in by_author.items():
        by_year: dict[int, int] = {}
        citation_history: dict[int, int] = {}
        for p in papers:
            by_year[p["year"]] = by_year.get(p["year"], 0) + 1
            citation_history[p["year"]] = citation_history.get(p["year"], 0) + p["citations"]
        peak_year = max(by_year, key=by_year.get)
        results.append(
            {
                "author": author,
                "peak_year": peak_year,
                "peak_papers": by_year[peak_year],
                "citation_history": citation_history,
            }
        )

    results.sort(key=lambda x: x["peak_papers"], reverse=True)
    return {"career": results[:limit]}


def local_citations(conn: sqlite3.Connection, project_id: int) -> dict:
    """Citations from within this corpus only (a paper in this project
    citing another paper in this project, matched by DOI). Distinct from
    'global citations' (cited_by_count from Scopus/OpenAlex, covering the
    whole literature). Will be 0 or near-0 for small corpora -- that's
    expected, not a bug."""
    rows = conn.execute(
        """
        SELECT citing.id AS citing_id, cited.id AS cited_id
        FROM papers AS citing
        JOIN paper_references ON paper_references.paper_id = citing.id
        JOIN reference_entries ON reference_entries.id = paper_references.reference_id
        JOIN papers AS cited ON cited.doi = reference_entries.doi
        WHERE citing.project_id = ? AND cited.project_id = ? AND reference_entries.doi IS NOT NULL
        """,
        (project_id, project_id),
    ).fetchall()
    counts: dict[int, int] = {}
    for r in rows:
        counts[r["cited_id"]] = counts.get(r["cited_id"], 0) + 1
    return {"local_citations_by_paper": counts, "total_local_citation_links": len(rows)}
