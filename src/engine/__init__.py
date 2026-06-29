import sqlite3

from engine import (
    authors,
    citations,
    countries,
    dataset,
    institutions,
    journals,
    keywords,
    publications,
    references,
)


def run_all(conn: sqlite3.Connection, project_id: int) -> dict:
    return {
        "dataset": dataset.get_overview(conn, project_id),
        "publications": publications.by_year(conn, project_id),
        "citations": citations.get_distribution(conn, project_id),
        "authors": authors.top_authors(conn, project_id),
        "journals": journals.top_journals(conn, project_id),
        "institutions": institutions.top_institutions(conn, project_id),
        "countries": countries.top_countries(conn, project_id),
        "keywords": keywords.top_keywords(conn, project_id),
        "references": references.most_cited_references(conn, project_id),
    }
