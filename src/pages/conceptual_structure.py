import dash
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import keywords, thematic
from pages.analysis_shared import CHART_LAYOUT, GROUP_COLORS, top_n_control
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/conceptual-structure", name="Conceptual Structure")


def _keyword_section(conn, project_id, top_n):
    data = keywords.top_keywords(conn, project_id, limit=top_n)

    if not data["keywords"]:
        return [html.Div(data["note"], className="coming-soon")]

    fig = go.Figure(
        go.Bar(
            x=[k["papers"] for k in data["keywords"]],
            y=[k["keyword"] for k in data["keywords"]],
            orientation="h",
            marker_color="#3F8F66",
        )
    )
    fig.update_layout(**{**CHART_LAYOUT, "height": 500})

    return [
        biblio_panel(
            "concept-top-keywords",
            "Top Keywords / Concepts",
            summary_rows=[("Distinct keywords shown", len(data["keywords"]))],
            figure=fig,
            table_columns=["Keyword", "Papers"],
            table_rows=[{"Keyword": k["keyword"], "Papers": k["papers"]} for k in data["keywords"]],
            note="Sourced from PubMed MeSH terms, OpenAlex concepts, or PDF-extracted "
            "keyword lines, in that priority order.",
        )
    ]


def _thematic_section(conn, project_id):
    tm = thematic.thematic_map(conn, project_id)
    te = thematic.theme_evolution(conn, project_id)

    panels = []
    if tm["clusters"]:
        scatter_fig = go.Figure(
            go.Scatter(
                x=[c["centrality"] for c in tm["clusters"]],
                y=[c["density"] for c in tm["clusters"]],
                mode="markers+text",
                text=[f"Cluster {c['cluster_id']}" for c in tm["clusters"]],
                textposition="top center",
                marker=dict(
                    size=[8 + 2 * len(c["keywords"]) for c in tm["clusters"]],
                    color=GROUP_COLORS[: len(tm["clusters"])],
                ),
            )
        )
        scatter_fig.add_vline(x=tm["median_centrality"], line_dash="dash", line_color="#7DA0CA")
        scatter_fig.add_hline(y=tm["median_density"], line_dash="dash", line_color="#7DA0CA")
        scatter_fig.update_layout(**CHART_LAYOUT, xaxis_title="Centrality", yaxis_title="Density")

        panels.append(
            biblio_panel(
                "concept-thematic-map",
                "Thematic Map / Strategic Diagram",
                figure=scatter_fig,
                table_columns=["Cluster", "Quadrant", "Centrality", "Density", "Keywords"],
                table_rows=[
                    {
                        "Cluster": c["cluster_id"],
                        "Quadrant": c["quadrant"],
                        "Centrality": c["centrality"],
                        "Density": c["density"],
                        "Keywords": ", ".join(c["keywords"][:8]) + (" ..." if len(c["keywords"]) > 8 else ""),
                    }
                    for c in tm["clusters"]
                ],
                note="Bibliometrix-style strategic diagram: keyword clusters found via "
                "Louvain community detection on the co-occurrence network, plotted by "
                "Callon centrality (links to other clusters) vs density (internal "
                "cohesion). This is real co-word clustering, not the more rigorous MCA/ "
                "Correspondence Analysis bibliometrix also offers -- that's not "
                "implemented in this milestone.",
            )
        )
    else:
        panels.append(html.Div(tm.get("note", "No thematic clusters available."), className="coming-soon"))

    if te["periods"]:
        panels.append(
            biblio_panel(
                "concept-theme-evolution",
                "Theme / Concept Evolution",
                summary_rows=[
                    ("Period A", te["periods"][0]["period"]),
                    ("Period B", te["periods"][1]["period"]),
                    ("Emerging keywords (B only)", len(te["emerging"])),
                    ("Declining keywords (A only)", len(te["declining"])),
                    ("Persistent keywords (both)", len(te["persistent"])),
                ],
                table_columns=["Status", "Keyword"],
                table_rows=[{"Status": "Emerging", "Keyword": k} for k in te["emerging"][:30]]
                + [{"Status": "Declining", "Keyword": k} for k in te["declining"][:30]],
                note="Comparing keyword sets across the corpus's two year-halves -- "
                "a real but coarse periodization, since most corpora here span only "
                "1-3 distinct years.",
            )
        )
    else:
        panels.append(html.Div(te.get("note", "No theme evolution data available."), className="coming-soon"))

    return panels


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        keyword_panels = _keyword_section(conn, project_id, top_n)
        thematic_panels = _thematic_section(conn, project_id)

    return dcc.Tabs(
        [
            dcc.Tab(label="Keywords", children=keyword_panels),
            dcc.Tab(label="Thematic Map & Evolution", children=thematic_panels),
        ]
    )


def layout():
    return html.Div(
        [
            html.H3("Conceptual Structure"),
            top_n_control("concept-top-n", default=20, min_n=10, max_n=50, step=10),
            html.Div(id="concept-content", children=_render(20)),
        ]
    )


@dash.callback(Output("concept-content", "children"), Input("concept-top-n", "value"))
def update_concept(top_n):
    return _render(top_n)
