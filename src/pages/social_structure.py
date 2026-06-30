import dash
from dash import dcc, html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import countries, social_networks
from engine.network_utils import centrality_table, detect_communities, network_metrics
from pages.analysis_shared import stacked_bar_from_pivot, top_n_control
from repository.project_repository import ProjectRepository
from visualizations.network import network_chart
from visualizations.worldmap import choropleth_chart

# Matches biblioshiny's real Social Structure scope (collabNetwork,
# collabWorldMap) -- country production counts live under Authors, not here.
dash.register_page(__name__, path="/social-structure", name="Social Structure")

_NETWORK_NOTES = {
    "author": "Edge = two authors appearing on the same paper.",
    "institution": "Edge = two institutions appearing on the same paper.",
    "country": "Edge = two countries appearing on the same paper (via institution affiliations).",
}


def _collab_worldmap_section(conn, project_id, top_n):
    """Matches biblioshiny's collabWorldMap -- collaboration intensity by
    country (paper count via institution affiliation), shown as a map."""
    data = countries.top_countries(conn, project_id, limit=top_n)
    if not data["countries"]:
        return [html.Div(data["note"], className="coming-soon")]

    fig = choropleth_chart([c["country"] for c in data["countries"]], [c["papers"] for c in data["countries"]], title="Collaboration World Map")
    return [
        biblio_panel(
            "social-collab-worldmap",
            "Collaboration World Map",
            summary_rows=[("Distinct countries shown", len(data["countries"]))],
            figure=fig,
            table_columns=["Country", "Papers"],
            table_rows=[{"Country": c["country"], "Papers": c["papers"]} for c in data["countries"]],
        )
    ]


def _network_section(conn, project_id, network_type, panel_prefix):
    graph, _ = social_networks.build_social_network(conn, project_id, network_type)
    if graph.number_of_nodes() == 0:
        return [html.Div("No data available for this network.", className="coming-soon")]

    communities = detect_communities(graph)
    fig = network_chart(graph, communities)
    metrics = network_metrics(graph)
    centrality = centrality_table(graph)

    return [
        biblio_panel(
            f"{panel_prefix}-network",
            f"{network_type.title()} Collaboration Network",
            summary_rows=[
                ("Nodes", metrics["nodes"]),
                ("Edges", metrics["edges"]),
                ("Density", metrics["density"]),
                ("Connected components", metrics["connected_components"]),
                ("Communities detected (Louvain)", len(set(communities.values())) if communities else 0),
                ("Clustering coefficient", metrics["clustering_coefficient"]),
                ("Diameter (largest component)", metrics["diameter"]),
                ("Avg path length (largest component)", metrics["average_path_length"]),
            ],
            figure=fig,
            table_columns=["Node", "Degree", "Betweenness", "Closeness", "Eigenvector", "PageRank"],
            table_rows=[
                {
                    "Node": c["node"], "Degree": c["degree"], "Betweenness": c["betweenness"],
                    "Closeness": c["closeness"], "Eigenvector": c["eigenvector"], "PageRank": c["pagerank"],
                }
                for c in centrality
            ],
            note=_NETWORK_NOTES.get(network_type, ""),
        )
    ]


def _timeline_section(conn, project_id):
    timeline = social_networks.collaboration_timeline(conn, project_id)
    if not timeline:
        return [html.Div("No year-level collaboration data available.", className="coming-soon")]

    return [
        biblio_panel(
            "social-collab-timeline",
            "Collaboration Timeline (Single vs Multi-institution Papers)",
            figure=stacked_bar_from_pivot(timeline),
            table_columns=["Year", "Type", "Papers"],
            table_rows=[{"Year": y, "Type": t, "Papers": c} for y, td in timeline.items() for t, c in td.items()],
        )
    ]


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        author_net_panels = _network_section(conn, project_id, "author", "social-author")
        institution_net_panels = _network_section(conn, project_id, "institution", "social-institution")
        country_net_panels = _network_section(conn, project_id, "country", "social-country")
        worldmap_panels = _collab_worldmap_section(conn, project_id, top_n)
        timeline_panels = _timeline_section(conn, project_id)

    return dcc.Tabs(
        [
            dcc.Tab(label="Author Network", children=author_net_panels),
            dcc.Tab(label="Institution Network", children=institution_net_panels),
            dcc.Tab(label="Country Network", children=country_net_panels),
            dcc.Tab(label="Collaboration World Map", children=worldmap_panels),
            dcc.Tab(label="Collaboration Timeline", children=timeline_panels),
        ]
    )


def layout():
    return html.Div(
        [
            html.H3("Social Structure"),
            top_n_control("social-top-n", default=10, min_n=5, max_n=30, step=5),
            html.Div(id="social-content", children=_render(10)),
        ]
    )


@dash.callback(Output("social-content", "children"), Input("social-top-n", "value"))
def update_social(top_n):
    return _render(top_n)
