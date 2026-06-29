import sqlite3

import numpy as np


def get_distribution(conn: sqlite3.Connection, project_id: int, limit: int = 10) -> dict:
    rows = conn.execute(
        "SELECT title, cited_by_count FROM papers WHERE project_id = ? AND cited_by_count IS NOT NULL",
        (project_id,),
    ).fetchall()

    if not rows:
        return {"total_citations": 0, "average": 0, "median": 0, "percentiles": {}, "top_cited": []}

    values = np.array([r["cited_by_count"] for r in rows])
    top_cited = sorted(
        ({"title": r["title"], "citations": r["cited_by_count"]} for r in rows),
        key=lambda x: x["citations"],
        reverse=True,
    )[:limit]

    return {
        "total_citations": int(values.sum()),
        "average": round(float(values.mean()), 2),
        "median": round(float(np.median(values)), 2),
        "percentiles": {
            "p25": round(float(np.percentile(values, 25)), 2),
            "p50": round(float(np.percentile(values, 50)), 2),
            "p75": round(float(np.percentile(values, 75)), 2),
            "p90": round(float(np.percentile(values, 90)), 2),
        },
        "top_cited": top_cited,
    }
