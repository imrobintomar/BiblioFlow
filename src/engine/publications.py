import sqlite3

import numpy as np

MIN_POINTS_FOR_FORECAST = 4


def by_year(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT year, COUNT(*) AS count FROM papers
        WHERE project_id = ? AND year IS NOT NULL
        GROUP BY year ORDER BY year
        """,
        (project_id,),
    ).fetchall()
    years = {str(r["year"]): r["count"] for r in rows}

    growth_rate = None
    sorted_years = sorted(years.keys())
    if len(sorted_years) >= 2:
        first, last = years[sorted_years[0]], years[sorted_years[-1]]
        n_periods = int(sorted_years[-1]) - int(sorted_years[0])
        if first > 0 and n_periods > 0:
            growth_rate = round(((last / first) ** (1 / n_periods) - 1) * 100, 2)

    return {"by_year": years, "cagr_percent": growth_rate}


def by_month(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT substr(publication_date, 1, 7) AS month, COUNT(*) AS count
        FROM papers
        WHERE project_id = ? AND publication_date IS NOT NULL AND length(publication_date) >= 7
        GROUP BY month ORDER BY month
        """,
        (project_id,),
    ).fetchall()
    return {"by_month": {r["month"]: r["count"] for r in rows}}


def moving_average(by_year_counts: dict, window: int = 2) -> dict:
    sorted_years = sorted(by_year_counts.keys())
    values = [by_year_counts[y] for y in sorted_years]

    if len(values) < window:
        return {"years": sorted_years, "moving_average": values}

    averaged = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start : i + 1]
        averaged.append(round(sum(chunk) / len(chunk), 2))

    return {"years": sorted_years, "moving_average": averaged}


def forecast_next_period(by_year_counts: dict) -> dict:
    sorted_years = sorted(by_year_counts.keys())

    if len(sorted_years) < MIN_POINTS_FOR_FORECAST:
        return {
            "forecast": None,
            "note": f"Need at least {MIN_POINTS_FOR_FORECAST} years of data for a "
            f"forecast; only {len(sorted_years)} available.",
        }

    x = np.array([int(y) for y in sorted_years])
    y = np.array([by_year_counts[year] for year in sorted_years])
    slope, intercept = np.polyfit(x, y, 1)
    next_year = x[-1] + 1
    predicted = max(0, round(slope * next_year + intercept))

    return {"forecast": {"year": int(next_year), "predicted_papers": int(predicted)}, "note": None}


def by_quarter(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT substr(publication_date, 1, 4) AS yr,
               ((CAST(substr(publication_date, 6, 2) AS INTEGER) - 1) / 3) + 1 AS q,
               COUNT(*) AS count
        FROM papers
        WHERE project_id = ? AND publication_date IS NOT NULL AND length(publication_date) >= 7
        GROUP BY yr, q ORDER BY yr, q
        """,
        (project_id,),
    ).fetchall()
    return {"by_quarter": {f"{r['yr']}-Q{r['q']}": r["count"] for r in rows}}


def by_decade(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT (year / 10) * 10 AS decade, COUNT(*) AS count
        FROM papers WHERE project_id = ? AND year IS NOT NULL
        GROUP BY decade ORDER BY decade
        """,
        (project_id,),
    ).fetchall()
    return {"by_decade": {f"{r['decade']}s": r["count"] for r in rows}}


def cumulative(by_year_counts: dict) -> dict:
    sorted_years = sorted(by_year_counts.keys())
    running = 0
    cumulative_counts = {}
    for y in sorted_years:
        running += by_year_counts[y]
        cumulative_counts[y] = running
    return {"cumulative": cumulative_counts}


def density(conn: sqlite3.Connection, project_id: int) -> dict:
    row = conn.execute(
        "SELECT COUNT(*) AS total, MIN(year) AS min_year, MAX(year) AS max_year "
        "FROM papers WHERE project_id = ? AND year IS NOT NULL",
        (project_id,),
    ).fetchone()
    if not row or not row["total"] or row["min_year"] is None:
        return {"papers_per_year": 0.0, "span_years": 0}
    span = max(1, row["max_year"] - row["min_year"] + 1)
    return {"papers_per_year": round(row["total"] / span, 2), "span_years": span}


def heatmap(conn: sqlite3.Connection, project_id: int) -> dict:
    """Year x month publication counts -- used for both the heatmap and the
    calendar view (true day-level publication dates aren't reliably
    available from any current source, so month granularity is the floor)."""
    rows = conn.execute(
        """
        SELECT substr(publication_date, 1, 4) AS yr, substr(publication_date, 6, 2) AS mo, COUNT(*) AS count
        FROM papers
        WHERE project_id = ? AND publication_date IS NOT NULL AND length(publication_date) >= 7
        GROUP BY yr, mo
        """,
        (project_id,),
    ).fetchall()
    years = sorted({r["yr"] for r in rows})
    months = [f"{m:02d}" for m in range(1, 13)]
    matrix = [[0] * 12 for _ in years]
    for r in rows:
        yi = years.index(r["yr"])
        mi = int(r["mo"]) - 1
        matrix[yi][mi] = r["count"]
    return {"years": years, "months": months, "matrix": matrix}


def growth_by_document_type(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT year, document_type, COUNT(*) AS count FROM papers
        WHERE project_id = ? AND year IS NOT NULL AND document_type IS NOT NULL
        GROUP BY year, document_type ORDER BY year
        """,
        (project_id,),
    ).fetchall()
    return _pivot_by_year(rows, "document_type")


def growth_by_country(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT papers.year AS year, countries.name AS group_name, COUNT(DISTINCT papers.id) AS count
        FROM papers
        JOIN paper_institutions ON paper_institutions.paper_id = papers.id
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN countries ON countries.id = institutions.country_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY papers.year, countries.id ORDER BY papers.year
        """,
        (project_id,),
    ).fetchall()
    return _pivot_by_year(rows, "group_name")


def growth_by_institution(conn: sqlite3.Connection, project_id: int, limit: int = 8) -> dict:
    top_institutions = [
        r["name"]
        for r in conn.execute(
            """
            SELECT institutions.name, COUNT(DISTINCT papers.id) AS c FROM paper_institutions
            JOIN institutions ON institutions.id = paper_institutions.institution_id
            JOIN papers ON papers.id = paper_institutions.paper_id
            WHERE papers.project_id = ? GROUP BY institutions.id ORDER BY c DESC LIMIT ?
            """,
            (project_id, limit),
        ).fetchall()
    ]
    if not top_institutions:
        return {}
    placeholders = ",".join("?" for _ in top_institutions)
    rows = conn.execute(
        f"""
        SELECT papers.year AS year, institutions.name AS group_name, COUNT(DISTINCT papers.id) AS count
        FROM papers
        JOIN paper_institutions ON paper_institutions.paper_id = papers.id
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL AND institutions.name IN ({placeholders})
        GROUP BY papers.year, institutions.id ORDER BY papers.year
        """,
        (project_id, *top_institutions),
    ).fetchall()
    return _pivot_by_year(rows, "group_name")


def growth_by_journal(conn: sqlite3.Connection, project_id: int, limit: int = 8) -> dict:
    rows = conn.execute(
        """
        SELECT papers.year AS year, journals.name AS group_name, COUNT(*) AS count
        FROM papers JOIN journals ON journals.id = papers.journal_id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY papers.year, journals.id ORDER BY papers.year
        """,
        (project_id,),
    ).fetchall()
    return _pivot_by_year(rows, "group_name")


def _pivot_by_year(rows, group_column: str) -> dict:
    """rows: sqlite3.Row with columns (year, <group_column>, count) -> {year: {group: count}}"""
    pivot: dict[str, dict[str, int]] = {}
    for r in rows:
        year = str(r["year"])
        group = r[group_column] or "Unknown"
        pivot.setdefault(year, {})[group] = r["count"]
    return pivot
