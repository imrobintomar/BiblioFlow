import sqlite3

# CrossRef's `type` taxonomy -> human-readable labels matching the
# bibliometrix-style document-type vocabulary (Article/Review/Book/etc.)
DOCUMENT_TYPE_LABELS = {
    "journal-article": "Article",
    "journal-issue": "Journal Issue",
    "proceedings-article": "Conference Paper",
    "book": "Book",
    "book-chapter": "Book Chapter",
    "monograph": "Book",
    "edited-book": "Book",
    "reference-book": "Book",
    "report": "Report",
    "dissertation": "Thesis",
    "dataset": "Dataset",
    "preprint": "Preprint",
    "posted-content": "Preprint",
    "peer-review": "Editorial",
    "letter": "Letter",
    "other": "Other",
}


def document_type_distribution(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        "SELECT document_type, COUNT(*) AS c FROM papers WHERE project_id = ? GROUP BY document_type",
        (project_id,),
    ).fetchall()
    distribution: dict[str, int] = {}
    for r in rows:
        label = DOCUMENT_TYPE_LABELS.get(r["document_type"], r["document_type"] or "Unknown")
        distribution[label] = distribution.get(label, 0) + r["c"]
    return {"distribution": distribution}


def open_access_breakdown(conn: sqlite3.Connection, project_id: int) -> dict:
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM papers WHERE project_id = ?", (project_id,)
    ).fetchone()["c"]

    rows = conn.execute(
        "SELECT oa_status, COUNT(*) AS c FROM papers WHERE project_id = ? AND oa_status IS NOT NULL GROUP BY oa_status",
        (project_id,),
    ).fetchall()
    by_status = {r["oa_status"].title(): r["c"] for r in rows}

    closed_count = conn.execute(
        "SELECT COUNT(*) AS c FROM papers WHERE project_id = ? AND (open_access IS NULL OR open_access = 0)",
        (project_id,),
    ).fetchone()["c"]
    if closed_count:
        by_status["Closed"] = closed_count

    open_count = conn.execute(
        "SELECT COUNT(*) AS c FROM papers WHERE project_id = ? AND open_access = 1", (project_id,)
    ).fetchone()["c"]

    return {
        "by_status": by_status,
        "open_pct": round(100 * open_count / total, 1) if total else 0.0,
        "closed_pct": round(100 * closed_count / total, 1) if total else 0.0,
    }


def license_distribution(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        "SELECT license, COUNT(*) AS c FROM papers WHERE project_id = ? AND license IS NOT NULL GROUP BY license",
        (project_id,),
    ).fetchall()
    return {"distribution": {r["license"]: r["c"] for r in rows}}
