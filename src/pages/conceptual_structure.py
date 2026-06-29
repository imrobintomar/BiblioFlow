import dash
import plotly.graph_objects as go
from dash import html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import keywords
from pages.analysis_shared import CHART_LAYOUT
from pages.analysis_shared import top_n_control
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/conceptual-structure", name="Conceptual Structure")


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        data = keywords.top_keywords(conn, project_id, limit=top_n)

    if not data["keywords"]:
        return html.Div(data["note"], className="coming-soon")

    fig = go.Figure(
        go.Bar(
            x=[k["papers"] for k in data["keywords"]],
            y=[k["keyword"] for k in data["keywords"]],
            orientation="h",
            marker_color="#3F8F66",
        )
    )
    fig.update_layout(**{**CHART_LAYOUT, "height": 500})

    return biblio_panel(
        "concept-top-keywords",
        "Top Keywords / Concepts",
        summary_rows=[("Distinct keywords shown", len(data["keywords"]))],
        figure=fig,
        table_columns=["Keyword", "Papers"],
        table_rows=[{"Keyword": k["keyword"], "Papers": k["papers"]} for k in data["keywords"]],
        note="Sourced from PubMed MeSH terms, OpenAlex concepts, or PDF-extracted "
        "keyword lines, in that priority order. Word clouds, thematic maps, and topic "
        "evolution (biblioshiny's full Conceptual Structure suite) are a future milestone.",
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
