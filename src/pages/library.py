import dash
import dash_ag_grid as dag
from dash import dcc, html

from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from repository.paper_repository import PaperRepository
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/library", name="Library")

COLUMN_DEFS = [
    {"field": "title", "headerName": "Title", "flex": 2, "filter": "agTextColumnFilter"},
    {"field": "authors_display", "headerName": "Authors", "flex": 1.5},
    {"field": "journal_name", "headerName": "Journal", "flex": 1, "filter": "agTextColumnFilter"},
    {"field": "year", "headerName": "Year", "width": 90, "filter": "agNumberColumnFilter"},
    {"field": "doi", "headerName": "DOI", "flex": 1},
    {
        "field": "cited_by_count",
        "headerName": "Citations",
        "width": 110,
        "filter": "agNumberColumnFilter",
    },
    {"field": "status", "headerName": "Status", "width": 130},
]


def _load_rows() -> list[dict]:
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        papers = PaperRepository(conn).list_papers(project_id)

    for p in papers:
        p["authors_display"] = ", ".join(p.get("authors", [])[:3]) + (
            " et al." if len(p.get("authors", [])) > 3 else ""
        )
        p["title_link"] = f"/paper/{p['id']}"
    return papers


def layout():
    rows = _load_rows()
    return html.Div(
        [
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "16px",
                },
                children=[
                    html.Div(
                        [
                            html.H3("Library", style={"marginBottom": "2px"}),
                            html.P(
                                f"{len(rows)} paper(s) — click a row to open Paper Details.",
                                style={"color": "#5483B3", "margin": 0},
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.A(
                                "Export CSV",
                                href="/export/library.csv",
                                className="btn btn-outline-light btn-sm",
                                style={"marginRight": "8px"},
                            ),
                            html.A(
                                "Export Excel",
                                href="/export/library.xlsx",
                                className="btn btn-outline-light btn-sm",
                            ),
                        ]
                    ),
                ],
            ),
            dag.AgGrid(
                id="library-grid",
                columnDefs=COLUMN_DEFS,
                rowData=rows,
                defaultColDef={"sortable": True, "resizable": True, "filter": True},
                dashGridOptions={"pagination": True, "paginationPageSize": 15, "rowSelection": "single"},
                className="ag-theme-alpine",
                style={"height": "560px", "width": "100%"},
            ),
            dcc.Location(id="library-redirect"),
        ]
    )


@dash.callback(
    dash.Output("library-redirect", "href"),
    dash.Input("library-grid", "selectedRows"),
    prevent_initial_call=True,
)
def open_paper_details(selected_rows):
    if not selected_rows:
        return dash.no_update
    return f"/paper/{selected_rows[0]['id']}"
