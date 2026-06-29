import dash
from dash import dcc, html

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import clustering
from engine.network_utils import centrality_table, detect_communities, graph_figure, network_metrics
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/clustering", name="Clustering")

_NETWORK_LABELS = {
    "co_authorship": ("Co-authorship Network", "Edge = two authors appearing on the same paper."),
    "keyword_cooccurrence": ("Keyword Co-occurrence Network", "Edge = two keywords appearing on the same paper."),
    "bibliographic_coupling": (
        "Bibliographic Coupling Network",
        "Edge = two papers sharing at least one cited reference (resolved by DOI). Only "
        "Semantic Scholar references currently resolve to a DOI -- OpenAlex's "
        "referenced_works aren't DOI-resolved, so coupling strength is likely "
        "undercounted until that's added.",
    ),
    "citation": (
        "Citation Network (Local)",
        "Directed citing -> cited edges within this corpus only, matched by DOI. "
        "Expected to be sparse/empty for small or topically diverse corpora.",
    ),
}


def _network_panel(conn, project_id, network_type):
    label, note = _NETWORK_LABELS[network_type]
    graph, _ = clustering.build_network(conn, project_id, network_type)

    if graph.number_of_nodes() == 0:
        return html.Div(f"No data available for {label}. {note}", className="coming-soon")

    communities = detect_communities(graph)
    fig = graph_figure(graph, communities)
    metrics = network_metrics(graph)
    centrality = centrality_table(graph)

    return biblio_panel(
        f"cluster-{network_type}",
        label,
        summary_rows=[
            ("Nodes", metrics["nodes"]),
            ("Edges", metrics["edges"]),
            ("Density", metrics["density"]),
            ("Connected components", metrics["connected_components"]),
            ("Communities detected (Louvain)", len(set(communities.values())) if communities else 0),
            ("Clustering coefficient", metrics["clustering_coefficient"]),
            ("Diameter (largest component)", metrics["diameter"]),
            ("Avg path length (largest component)", metrics["average_path_length"]),
            ("Assortativity", metrics["assortativity"]),
        ],
        figure=fig,
        table_columns=["Node", "Degree", "Betweenness", "Closeness", "Eigenvector", "PageRank"],
        table_rows=[
            {
                "Node": c["node"][:60], "Degree": c["degree"], "Betweenness": c["betweenness"],
                "Closeness": c["closeness"], "Eigenvector": c["eigenvector"], "PageRank": c["pagerank"],
            }
            for c in centrality[:100]
        ],
        note=note,
    )


def layout():
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        co_authorship_panel = _network_panel(conn, project_id, "co_authorship")
        keyword_panel = _network_panel(conn, project_id, "keyword_cooccurrence")
        coupling_panel = _network_panel(conn, project_id, "bibliographic_coupling")
        citation_panel = _network_panel(conn, project_id, "citation")

    return html.Div(
        [
            html.H3("Clustering"),
            html.P(
                "Co-occurrence, citation, and bibliographic coupling networks, with "
                "full centrality measures (degree/betweenness/closeness/eigenvector/"
                "PageRank), network-level metrics, and Louvain community detection.",
                style={"color": "#5483B3"},
            ),
            dcc.Tabs(
                [
                    dcc.Tab(label="Co-authorship", children=[co_authorship_panel]),
                    dcc.Tab(label="Keyword Co-occurrence", children=[keyword_panel]),
                    dcc.Tab(label="Bibliographic Coupling", children=[coupling_panel]),
                    dcc.Tab(label="Citation Network", children=[citation_panel]),
                ]
            ),
        ]
    )
