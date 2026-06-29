import sqlite3
from collections import Counter

from config import DB_PATH, SCOPUS_API_KEY
from db import get_connection
from models import PipelineRecord


def load_all_records() -> list[PipelineRecord]:
    if not DB_PATH.exists():
        return []

    records: list[PipelineRecord] = []
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT record_json FROM pipeline_state ORDER BY filename")
        for row in cur.fetchall():
            try:
                records.append(PipelineRecord.model_validate_json(row["record_json"]))
            except ValueError:
                continue
    return records


def compute_kpis(records: list[PipelineRecord]) -> dict:
    authors: set[str] = set()
    journals: set[str] = set()
    citations = 0

    for r in records:
        if r.scopus:
            authors.update(r.scopus.authors)
            journals.add(r.scopus.source_title) if r.scopus.source_title else None
            citations += r.scopus.cited_by_count or 0
        elif r.crossref:
            authors.update(r.crossref.crossref_authors)
            journals.add(r.crossref.journal) if r.crossref.journal else None

    return {
        "papers": len(records),
        "authors": len(authors),
        "journals": len(journals),
        "citations": citations,
        "projects": 1,
    }


def publication_trend(records: list[PipelineRecord]) -> Counter:
    years = Counter()
    for r in records:
        year = None
        if r.scopus and r.scopus.publication_date:
            year = r.scopus.publication_date[:4]
        elif r.crossref and r.crossref.year:
            year = str(r.crossref.year)
        if year:
            years[year] += 1
    return years


def top_journals(records: list[PipelineRecord], limit: int = 5) -> Counter:
    journals = Counter()
    for r in records:
        journal = (r.scopus.source_title if r.scopus else None) or (
            r.crossref.journal if r.crossref else None
        )
        if journal:
            journals[journal] += 1
    return Counter(dict(journals.most_common(limit)))


def connection_status() -> dict:
    return {
        "sqlite": DB_PATH.exists(),
        "crossref": True,
        "scopus": bool(SCOPUS_API_KEY),
    }
