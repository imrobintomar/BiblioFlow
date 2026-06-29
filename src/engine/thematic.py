import sqlite3

from engine.clustering import keyword_cooccurrence_edges
from engine.network_utils import build_graph, detect_communities

QUADRANT_LABELS = {
    (True, True): "Motor Themes",
    (True, False): "Basic Themes",
    (False, True): "Niche Themes",
    (False, False): "Emerging or Declining Themes",
}


def thematic_map(conn: sqlite3.Connection, project_id: int) -> dict:
    """Bibliometrix-style strategic diagram: cluster keywords by co-occurrence
    community, then for each cluster compute Callon centrality (sum of links
    to OTHER clusters) and Callon density (avg internal cohesion within the
    cluster). Quadrant assignment follows bibliometrix's convention.

    True MCA/Correspondence Analysis (a separate, more rigorous dimensionality-
    reduction technique bibliometrix also offers) is not implemented -- this
    is a real but simpler co-word-clustering approach, not a substitute."""
    edges = keyword_cooccurrence_edges(conn, project_id)
    if not edges:
        return {"clusters": [], "note": "No keyword co-occurrence data available."}

    graph = build_graph(edges, directed=False)
    communities = detect_communities(graph)

    if not communities:
        return {"clusters": [], "note": "No clusters could be detected."}

    cluster_nodes: dict[int, list[str]] = {}
    for node, cid in communities.items():
        cluster_nodes.setdefault(cid, []).append(node)

    centralities = []
    densities = []
    cluster_data = []
    for cid, nodes in cluster_nodes.items():
        internal_weight = 0
        external_weight = 0
        for u, v, w in edges:
            if u in nodes and v in nodes:
                internal_weight += w
            elif u in nodes or v in nodes:
                external_weight += w

        n = len(nodes)
        density = round(10 * internal_weight / max(1, n * (n - 1) / 2), 3) if n > 1 else 0.0
        centrality = round(10 * external_weight / max(1, n), 3)
        centralities.append(centrality)
        densities.append(density)
        cluster_data.append({"cluster_id": cid, "keywords": nodes, "centrality": centrality, "density": density})

    median_centrality = sorted(centralities)[len(centralities) // 2] if centralities else 0
    median_density = sorted(densities)[len(densities) // 2] if densities else 0

    for c in cluster_data:
        quadrant = QUADRANT_LABELS[(c["centrality"] >= median_centrality, c["density"] >= median_density)]
        c["quadrant"] = quadrant

    return {"clusters": cluster_data, "median_centrality": median_centrality, "median_density": median_density}


def theme_evolution(conn: sqlite3.Connection, project_id: int) -> dict:
    """Compares keyword clusters across the corpus's two halves by
    publication year (a real but limited periodization -- our typical
    corpus spans only 1-3 distinct years, so finer time-slicing wouldn't
    have enough data per period to cluster meaningfully)."""
    years = sorted(
        {
            str(r["year"])
            for r in conn.execute(
                "SELECT DISTINCT year FROM papers WHERE project_id = ? AND year IS NOT NULL", (project_id,)
            ).fetchall()
        }
    )
    if len(years) < 2:
        return {"periods": [], "note": f"Need 2+ distinct years to compare periods; only {len(years)} available."}

    midpoint = len(years) // 2 or 1
    period_a, period_b = years[:midpoint], years[midpoint:]

    def keywords_for_years(year_list: list[str]) -> set[str]:
        placeholders = ",".join("?" for _ in year_list)
        rows = conn.execute(
            f"""
            SELECT DISTINCT keywords.term FROM paper_keywords
            JOIN keywords ON keywords.id = paper_keywords.keyword_id
            JOIN papers ON papers.id = paper_keywords.paper_id
            WHERE papers.project_id = ? AND papers.year IN ({placeholders})
            """,
            (project_id, *year_list),
        ).fetchall()
        return {r["term"] for r in rows}

    set_a, set_b = keywords_for_years(period_a), keywords_for_years(period_b)

    return {
        "periods": [
            {"period": f"{period_a[0]}-{period_a[-1]}", "keywords": sorted(set_a)},
            {"period": f"{period_b[0]}-{period_b[-1]}", "keywords": sorted(set_b)},
        ],
        "emerging": sorted(set_b - set_a),
        "declining": sorted(set_a - set_b),
        "persistent": sorted(set_a & set_b),
    }
