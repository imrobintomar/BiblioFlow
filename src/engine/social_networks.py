import sqlite3

from engine.clustering import co_authorship_edges
from engine.network_utils import build_graph


def institution_network_edges(conn: sqlite3.Connection, project_id: int) -> list[tuple[str, str, int]]:
    rows = conn.execute(
        """
        SELECT paper_institutions.paper_id AS paper_id, institutions.name AS institution
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()
    from itertools import combinations
    from collections import Counter

    by_paper: dict[int, set[str]] = {}
    for r in rows:
        by_paper.setdefault(r["paper_id"], set()).add(r["institution"])

    edge_counts: Counter = Counter()
    for institutions in by_paper.values():
        for a, b in combinations(sorted(institutions), 2):
            edge_counts[(a, b)] += 1
    return [(a, b, w) for (a, b), w in edge_counts.items()]


def country_network_edges(conn: sqlite3.Connection, project_id: int) -> list[tuple[str, str, int]]:
    rows = conn.execute(
        """
        SELECT paper_institutions.paper_id AS paper_id, countries.name AS country
        FROM paper_institutions
        JOIN institutions ON institutions.id = paper_institutions.institution_id
        JOIN countries ON countries.id = institutions.country_id
        JOIN papers ON papers.id = paper_institutions.paper_id
        WHERE papers.project_id = ?
        """,
        (project_id,),
    ).fetchall()
    from itertools import combinations
    from collections import Counter

    by_paper: dict[int, set[str]] = {}
    for r in rows:
        by_paper.setdefault(r["paper_id"], set()).add(r["country"])

    edge_counts: Counter = Counter()
    for countries in by_paper.values():
        for a, b in combinations(sorted(countries), 2):
            edge_counts[(a, b)] += 1
    return [(a, b, w) for (a, b), w in edge_counts.items()]


def build_social_network(conn: sqlite3.Connection, project_id: int, network_type: str):
    builders = {
        "author": co_authorship_edges,
        "institution": institution_network_edges,
        "country": country_network_edges,
    }
    edges = builders[network_type](conn, project_id)
    return build_graph(edges, directed=False), edges


def collaboration_timeline(conn: sqlite3.Connection, project_id: int) -> dict:
    """Multi-institution (collaborative) papers per year vs single-institution
    papers per year."""
    rows = conn.execute(
        """
        SELECT papers.year AS year, COUNT(DISTINCT paper_institutions.institution_id) AS n_institutions
        FROM papers
        LEFT JOIN paper_institutions ON paper_institutions.paper_id = papers.id
        WHERE papers.project_id = ? AND papers.year IS NOT NULL
        GROUP BY papers.id
        """,
        (project_id,),
    ).fetchall()

    by_year: dict[str, dict[str, int]] = {}
    for r in rows:
        year = str(r["year"])
        bucket = "Collaborative (2+ institutions)" if r["n_institutions"] > 1 else "Single institution"
        by_year.setdefault(year, {"Collaborative (2+ institutions)": 0, "Single institution": 0})
        by_year[year][bucket] += 1

    return by_year
