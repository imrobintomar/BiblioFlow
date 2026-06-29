import sqlite3

FIELD_COMPLETENESS_COLUMNS = {
    "title": "title",
    "doi": "doi",
    "journal": "journal_id",
    "year": "year",
    "citations": "cited_by_count",
    "abstract": "abstract",
    "publisher": "publisher_id",
    "open_access": "open_access",
}


def _scalar(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return list(row)[0] if row else None


def get_overview(conn: sqlite3.Connection, project_id: int) -> dict:
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM papers WHERE project_id = ?", (project_id,)
    ).fetchone()["c"]

    if total == 0:
        return {
            "total_papers": 0,
            "avg_citations": 0,
            "avg_authors": 0,
            "metadata_completeness": {},
        }

    avg_citations = conn.execute(
        "SELECT AVG(cited_by_count) AS a FROM papers WHERE project_id = ? AND cited_by_count IS NOT NULL",
        (project_id,),
    ).fetchone()["a"] or 0

    avg_authors = conn.execute(
        """
        SELECT AVG(author_count) AS a FROM (
            SELECT papers.id, COUNT(paper_authors.author_id) AS author_count
            FROM papers
            LEFT JOIN paper_authors ON paper_authors.paper_id = papers.id
            WHERE papers.project_id = ?
            GROUP BY papers.id
        )
        """,
        (project_id,),
    ).fetchone()["a"] or 0

    completeness = {}
    for label, column in FIELD_COMPLETENESS_COLUMNS.items():
        filled = conn.execute(
            f"SELECT COUNT(*) AS c FROM papers WHERE project_id = ? AND {column} IS NOT NULL",
            (project_id,),
        ).fetchone()["c"]
        completeness[label] = round(100 * filled / total, 1)

    has_authors = conn.execute(
        """
        SELECT COUNT(DISTINCT papers.id) AS c FROM papers
        JOIN paper_authors ON paper_authors.paper_id = papers.id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchone()["c"]
    completeness["authors"] = round(100 * has_authors / total, 1)

    has_institutions = conn.execute(
        """
        SELECT COUNT(DISTINCT papers.id) AS c FROM papers
        JOIN paper_institutions ON paper_institutions.paper_id = papers.id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchone()["c"]
    completeness["institutions"] = round(100 * has_institutions / total, 1)

    has_keywords = conn.execute(
        """
        SELECT COUNT(DISTINCT papers.id) AS c FROM papers
        JOIN paper_keywords ON paper_keywords.paper_id = papers.id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchone()["c"]
    completeness["keywords"] = round(100 * has_keywords / total, 1)

    has_country = conn.execute(
        """
        SELECT COUNT(DISTINCT papers.id) AS c FROM papers
        JOIN paper_institutions ON paper_institutions.paper_id = papers.id
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        WHERE papers.project_id = ? AND institutions.country_id IS NOT NULL
        """,
        (project_id,),
    ).fetchone()["c"]
    completeness["countries"] = round(100 * has_country / total, 1)

    overall = round(sum(completeness.values()) / len(completeness), 1)

    return {
        "total_papers": total,
        "avg_citations": round(avg_citations, 2),
        "avg_authors": round(avg_authors, 2),
        "metadata_completeness": completeness,
        "overall_completeness": overall,
    }


def get_module1_stats(conn: sqlite3.Connection, project_id: int) -> dict:
    """Full Module 1 -- Dashboard dataset-overview metrics, all computed
    from real warehouse data. Fields with no extraction path yet (e.g.
    average pages, when CrossRef doesn't supply a page range) report 0/None
    honestly rather than fabricating a number."""
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM papers WHERE project_id = ?", (project_id,)
    ).fetchone()["c"]

    if total == 0:
        return {"total_papers": 0}

    def count_distinct(table, join_col):
        return _scalar(
            conn,
            f"""
            SELECT COUNT(DISTINCT {table}.id) FROM {table}
            JOIN paper_{table} ON paper_{table}.{join_col} = {table}.id
            JOIN papers ON papers.id = paper_{table}.paper_id
            WHERE papers.project_id = ?
            """,
            (project_id,),
        ) or 0

    total_authors = count_distinct("authors", "author_id")
    total_journals = _scalar(
        conn,
        "SELECT COUNT(DISTINCT journal_id) FROM papers WHERE project_id = ? AND journal_id IS NOT NULL",
        (project_id,),
    ) or 0
    total_institutions = count_distinct("institutions", "institution_id")
    total_countries = _scalar(
        conn,
        """
        SELECT COUNT(DISTINCT institutions.country_id) FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ? AND institutions.country_id IS NOT NULL
        """,
        (project_id,),
    ) or 0
    total_publishers = _scalar(
        conn,
        "SELECT COUNT(DISTINCT publisher_id) FROM papers WHERE project_id = ? AND publisher_id IS NOT NULL",
        (project_id,),
    ) or 0
    total_references = _scalar(
        conn,
        """
        SELECT COUNT(*) FROM paper_references
        JOIN papers ON papers.id = paper_references.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ) or 0
    total_keywords = count_distinct("keywords", "keyword_id")
    total_citations = _scalar(
        conn,
        "SELECT SUM(cited_by_count) FROM papers WHERE project_id = ?", (project_id,)
    ) or 0

    avg_citations = _scalar(
        conn,
        "SELECT AVG(cited_by_count) FROM papers WHERE project_id = ? AND cited_by_count IS NOT NULL",
        (project_id,),
    ) or 0

    author_counts = [
        r["c"]
        for r in conn.execute(
            """
            SELECT papers.id, COUNT(paper_authors.author_id) AS c
            FROM papers LEFT JOIN paper_authors ON paper_authors.paper_id = papers.id
            WHERE papers.project_id = ? GROUP BY papers.id
            """,
            (project_id,),
        ).fetchall()
    ]
    avg_authors = round(sum(author_counts) / len(author_counts), 2) if author_counts else 0
    single_authored = sum(1 for c in author_counts if c == 1)
    multi_authored = sum(1 for c in author_counts if c > 1)
    multi_author_total = sum(c for c in author_counts if c > 1)
    collaboration_index = round(multi_author_total / multi_authored, 2) if multi_authored else 0.0

    open_access_count = _scalar(
        conn, "SELECT COUNT(*) FROM papers WHERE project_id = ? AND open_access = 1", (project_id,)
    ) or 0
    open_access_pct = round(100 * open_access_count / total, 1)

    avg_references = round(total_references / total, 2)
    avg_keywords = round(
        _scalar(
            conn,
            """
            SELECT CAST(COUNT(*) AS REAL) / COUNT(DISTINCT papers.id) FROM paper_keywords
            JOIN papers ON papers.id = paper_keywords.paper_id WHERE papers.project_id = ?
            """,
            (project_id,),
        )
        or 0,
        2,
    )

    avg_pages = _scalar(
        conn,
        "SELECT AVG(page_count) FROM papers WHERE project_id = ? AND page_count IS NOT NULL",
        (project_id,),
    )
    avg_word_count = _scalar(
        conn,
        "SELECT AVG(word_count) FROM papers WHERE project_id = ? AND word_count IS NOT NULL",
        (project_id,),
    )

    years = [
        r["year"]
        for r in conn.execute(
            "SELECT year FROM papers WHERE project_id = ? AND year IS NOT NULL", (project_id,)
        ).fetchall()
    ]
    publication_span = f"{min(years)}-{max(years)}" if years else None

    growth_rate = None
    if years and len(set(years)) >= 2:
        from collections import Counter

        counts = Counter(years)
        sorted_years = sorted(counts.keys())
        first, last = counts[sorted_years[0]], counts[sorted_years[-1]]
        n_periods = sorted_years[-1] - sorted_years[0]
        if first > 0 and n_periods > 0:
            growth_rate = round(((last / first) ** (1 / n_periods) - 1) * 100, 2)

    duplicate_dois = _scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT doi FROM papers WHERE project_id = ? AND doi IS NOT NULL
            GROUP BY doi HAVING COUNT(*) > 1
        )
        """,
        (project_id,),
    ) or 0
    duplicate_paper_count = _scalar(
        conn,
        """
        SELECT SUM(cnt) FROM (
            SELECT COUNT(*) AS cnt FROM papers WHERE project_id = ? AND doi IS NOT NULL
            GROUP BY doi HAVING COUNT(*) > 1
        )
        """,
        (project_id,),
    ) or 0
    duplication_rate = round(100 * duplicate_paper_count / total, 1)

    metadata_confidence = _scalar(
        conn,
        """
        SELECT AVG(field_provenance.confidence) FROM field_provenance
        JOIN papers ON papers.id = field_provenance.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    )

    source_distribution = {
        r["source"]: r["c"]
        for r in conn.execute(
            """
            SELECT field_provenance.source, COUNT(*) AS c FROM field_provenance
            JOIN papers ON papers.id = field_provenance.paper_id
            WHERE papers.project_id = ? GROUP BY field_provenance.source
            """,
            (project_id,),
        ).fetchall()
    }
    source_distribution["pdf_extraction"] = total  # every paper has at least PDF-sourced fields

    overview = get_overview(conn, project_id)

    return {
        "total_papers": total,
        "total_authors": total_authors,
        "total_journals": total_journals,
        "total_institutions": total_institutions,
        "total_countries": total_countries,
        "total_publishers": total_publishers,
        "total_references": total_references,
        "total_keywords": total_keywords,
        "total_citations": total_citations,
        "avg_citations": round(avg_citations, 2),
        "avg_authors": avg_authors,
        "collaboration_index": collaboration_index,
        "single_authored": single_authored,
        "multi_authored": multi_authored,
        "open_access_pct": open_access_pct,
        "avg_references": avg_references,
        "avg_keywords": avg_keywords,
        "avg_pages": round(avg_pages, 1) if avg_pages else None,
        "avg_word_count": round(avg_word_count) if avg_word_count else None,
        "publication_span": publication_span,
        "annual_growth_rate": growth_rate,
        "cagr": growth_rate,
        "duplication_rate": duplication_rate,
        "metadata_completeness": overview.get("overall_completeness", 0),
        "metadata_confidence": round(metadata_confidence * 100, 1) if metadata_confidence else None,
        "source_distribution": source_distribution,
    }
