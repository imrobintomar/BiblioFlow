import dash
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import citations, funding, references
from pages.analysis_shared import CHART_LAYOUT, top_n_control
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/documents", name="Documents")


def _citation_section(conn, project_id, limit):
    cit_data = citations.get_distribution(conn, project_id, limit=limit)

    hist_fig = go.Figure(
        go.Bar(
            x=[p["title"][:30] + "…" if len(p["title"]) > 30 else p["title"] for p in cit_data["top_cited"]],
            y=[p["citations"] for p in cit_data["top_cited"]],
            marker_color="#D97706",
        )
    )
    hist_fig.update_layout(**CHART_LAYOUT)

    percentile_rows = [
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "padding": "6px 0"},
            children=[html.Span(k.upper()), html.Span(str(v))],
        )
        for k, v in cit_data["percentiles"].items()
    ]

    return [
        html.Div(
            className="panel-card",
            children=[
                html.H5("Citation Summary"),
                html.P(f"Total citations: {cit_data['total_citations']}"),
                html.P(f"Average: {cit_data['average']}"),
                html.P(f"Median: {cit_data['median']}"),
            ],
        ),
        html.Div(className="panel-card", children=[html.H5("Citation Percentiles"), *percentile_rows]),
        biblio_panel(
            "doc-most-cited", "Most Global Cited Documents",
            figure=hist_fig if cit_data["top_cited"] else None,
            table_columns=["Title", "Citations"],
            table_rows=[{"Title": p["title"], "Citations": p["citations"]} for p in cit_data["top_cited"]],
        ) if cit_data["top_cited"] else html.Div("No citation data yet.", className="coming-soon"),
    ]


def _reference_section(conn, project_id, limit):
    data = references.most_cited_references(conn, project_id, limit=limit)
    rows = conn.execute(
        "SELECT COUNT(*) AS c FROM paper_references JOIN papers ON papers.id = paper_references.paper_id WHERE papers.project_id = ?",
        (project_id,),
    ).fetchone()
    total_refs = rows["c"] if rows else 0

    return [
        biblio_panel(
            "doc-most-cited-refs", "Most Cited References (within this corpus)",
            summary_rows=[("Total reference links captured", total_refs)],
            table_columns=["DOI", "Times Cited"],
            table_rows=[{"DOI": r["doi"], "Times Cited": r["times_cited"]} for r in data["references"]],
            note=data["note"] + " Most references are sourced from OpenAlex/Semantic "
            "Scholar (not yet resolved to a shared DOI namespace across both, so "
            "'most cited within this corpus' under-counts until that resolution is added).",
        ) if data["references"] else html.Div(data["note"], className="coming-soon"),
    ]


def _funding_section(conn, project_id, limit):
    data = funding.top_funders(conn, project_id, limit=limit)
    if not data["funders"]:
        return [html.Div("No funders detected yet.", className="coming-soon")]

    rows = [
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "padding": "6px 0"},
            children=[html.Span(f["funder"]), html.Span(str(f["papers"]))],
        )
        for f in data["funders"]
    ]
    return [
        html.Div(className="panel-card", children=[html.H5("Top Funders"), *rows]),
        html.P(data["note"], style={"color": "#5483B3", "fontSize": "12px"}),
    ]


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        citation_panels = _citation_section(conn, project_id, top_n)
        reference_panels = _reference_section(conn, project_id, top_n)
        funding_panels = _funding_section(conn, project_id, top_n)

    return dcc.Tabs(
        [
            dcc.Tab(label="Citations", children=citation_panels),
            dcc.Tab(label="References", children=reference_panels),
            dcc.Tab(label="Funding", children=funding_panels),
        ]
    )


def layout():
    return html.Div(
        [
            html.H3("Documents"),
            top_n_control("documents-top-n", default=10, min_n=5, max_n=30, step=5),
            html.Div(id="documents-content", children=_render(10)),
        ]
    )


@dash.callback(Output("documents-content", "children"), Input("documents-top-n", "value"))
def update_documents(top_n):
    return _render(top_n)
