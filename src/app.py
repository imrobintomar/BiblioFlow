import dash
import dash_bootstrap_components as dbc
from dash import Dash, html
from flask import Response, request

from components import build_sidebar, build_status_footer, build_topbar
from data_loader import connection_status
from services.paper_export_service import PaperExportService
from utils import export_cache
from utils.export_utils import rows_to_csv

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="pages",
    external_stylesheets=[dbc.themes.FLATLY],
    title="BiblioFlow",
)

app.layout = html.Div(
    [
        build_topbar(),
        html.Div(
            className="app-shell",
            children=[
                build_sidebar(),
                html.Div(dash.page_container, className="main-content"),
            ],
        ),
        build_status_footer(connection_status()),
    ]
)

_export_service = PaperExportService()


@app.server.route("/export/library.csv")
def export_library_csv():
    return Response(
        _export_service.library_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=library.csv"},
    )


@app.server.route("/export/library.xlsx")
def export_library_xlsx():
    return Response(
        _export_service.library_excel(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=library.xlsx"},
    )


@app.server.route("/export/paper/<int:paper_id>.json")
def export_paper_json(paper_id: int):
    return Response(
        _export_service.paper_json(paper_id),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=paper_{paper_id}.json"},
    )


@app.server.route("/export/panel.csv")
def export_panel_csv():
    panel_id = request.args.get("panel", "")
    cached = export_cache.get(panel_id)
    if not cached:
        return Response("Panel data not available -- reload the page and try again.", status=404)
    columns, rows = cached
    return Response(
        rows_to_csv(rows, columns),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={panel_id}.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
