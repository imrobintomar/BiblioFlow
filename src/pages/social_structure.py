import dash
from dash import html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import countries
from pages.analysis_shared import bar_figure, top_n_control
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/social-structure", name="Social Structure")


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        data = countries.top_countries(conn, project_id, limit=top_n)

    if not data["countries"]:
        return html.Div(data["note"], className="coming-soon")

    fig = bar_figure([c["papers"] for c in data["countries"]], [c["country"] for c in data["countries"]], orientation="h")

    return biblio_panel(
        "social-countries",
        "Country Collaboration / Most Productive Countries",
        summary_rows=[("Distinct countries shown", len(data["countries"]))],
        figure=fig,
        table_columns=["Country", "Papers"],
        table_rows=[{"Country": c["country"], "Papers": c["papers"]} for c in data["countries"]],
        note="Collaboration network maps and SCP/MCP collaboration-type breakdowns "
        "(biblioshiny's full Social Structure suite) are a future milestone -- this "
        "view shows paper counts per country (via institution affiliations) today.",
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
