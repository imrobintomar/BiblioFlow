import dash
from dash import html

from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from repository.paper_repository import PaperRepository

dash.register_page(__name__, path_template="/paper/<paper_id>", name="Paper Details")


def _field(label: str, value) -> html.Div:
    return html.Div(
        style={"padding": "8px 0", "borderBottom": "1px solid #7DA0CA"},
        children=[
            html.Span(label, style={"color": "#5483B3", "fontSize": "12px", "display": "block"}),
            html.Span(value if value not in (None, "", []) else "—", style={"fontSize": "14px"}),
        ],
    )


def layout(paper_id: str | None = None):
    if paper_id is None:
        return html.Div("No paper selected.", className="coming-soon")

    with get_connection(WAREHOUSE_DB_PATH) as conn:
        paper = PaperRepository(conn).get_paper(int(paper_id))

    if not paper:
        return html.Div(f"Paper {paper_id} not found.", className="coming-soon")

    return html.Div(
        [
            html.A("← Back to Library", href="/library", style={"color": "#052659"}),
            html.H3(paper.get("title") or "(untitled)", style={"marginTop": "10px"}),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Metadata"),
                    _field("DOI", paper.get("doi")),
                    _field("Journal", paper.get("journal_name")),
                    _field("Year", paper.get("year")),
                    _field("Publication Date", paper.get("publication_date")),
                    _field("Citation Count", paper.get("cited_by_count")),
                    _field("EID (Scopus)", paper.get("eid")),
                    _field("Pipeline Status", paper.get("status")),
                    _field("Source", paper.get("source")),
                    _field("Error", paper.get("error")),
                ],
            ),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Authors"),
                    html.Ul([html.Li(a) for a in paper.get("authors", [])])
                    if paper.get("authors")
                    else html.P("No authors recorded.", className="coming-soon"),
                ],
            ),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Institutions"),
                    html.Ul([html.Li(i) for i in paper.get("institutions", [])])
                    if paper.get("institutions")
                    else html.P("No institutions recorded.", className="coming-soon"),
                ],
            ),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Abstract, Keywords & References"),
                    html.P(
                        "Not available -- requires Scopus Abstract Retrieval "
                        "(institutional access), not captured by the current "
                        "Search-API-only integration.",
                        className="coming-soon",
                    ),
                ],
            ),
            html.A(
                "Export this paper (JSON)",
                href=f"/export/paper/{paper_id}.json",
                className="btn btn-outline-light btn-sm",
            ),
        ]
    )
