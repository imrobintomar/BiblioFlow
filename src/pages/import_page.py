import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

from config import PDF_DIR
from services.import_service import ImportService

dash.register_page(__name__, path="/import", name="Import")

_import_service = ImportService()


def layout():
    pdf_files = sorted(PDF_DIR.glob("*.pdf")) if PDF_DIR.exists() else []
    return html.Div(
        [
            html.H3("Import"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("PDF Folder"),
                    html.P(str(PDF_DIR), style={"color": "#6E8898", "fontFamily": "monospace"}),
                    html.P(f"{len(pdf_files)} PDF(s) found"),
                    html.Ul([html.Li(p.name) for p in pdf_files]) if pdf_files else None,
                ],
            ),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Run Pipeline"),
                    html.P(
                        "Extracts DOI/title, verifies via CrossRef, enriches via Scopus, "
                        "for any new or changed PDFs in the folder above. Runs in the "
                        "background -- this page polls for progress.",
                        style={"color": "#6E8898"},
                    ),
                    html.Button("Run Pipeline", id="run-pipeline-btn", className="btn btn-primary"),
                    dcc.Store(id="active-job-id"),
                    dcc.Interval(id="job-poll-interval", interval=1500, disabled=True),
                    html.Div(id="run-pipeline-output", style={"marginTop": "14px"}),
                ],
            ),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Other import sources"),
                    html.P(
                        "Import from Scopus / Web of Science / PubMed / RIS / BibTeX — coming soon.",
                        className="coming-soon",
                    ),
                ],
            ),
        ]
    )


@dash.callback(
    Output("active-job-id", "data"),
    Output("job-poll-interval", "disabled"),
    Input("run-pipeline-btn", "n_clicks"),
    prevent_initial_call=True,
)
def start_import(n_clicks):
    job_id = _import_service.start_import(PDF_DIR, force=False)
    return job_id, False


@dash.callback(
    Output("run-pipeline-output", "children"),
    Output("job-poll-interval", "disabled", allow_duplicate=True),
    Input("job-poll-interval", "n_intervals"),
    State("active-job-id", "data"),
    prevent_initial_call=True,
)
def poll_job(n_intervals, job_id):
    if not job_id:
        return "", True

    job = _import_service.get_job(job_id)
    if not job:
        return "Job not found.", True

    progress_pct = round((job["progress"] or 0) * 100)
    bar = html.Div(
        style={"background": "#E4ECF0", "borderRadius": "6px", "overflow": "hidden", "height": "8px"},
        children=html.Div(
            style={
                "width": f"{progress_pct}%",
                "background": "#567C8D",
                "height": "100%",
            }
        ),
    )

    status_text = html.P(
        f"{job['status'].title()} — {job['message'] or ''} ({progress_pct}%)",
        style={"color": "#6E8898", "marginTop": "8px"},
    )

    if job["status"] in ("done", "failed"):
        color = "#3F8F66" if job["status"] == "done" else "#B3261E"
        return (
            html.Div([bar, html.P(job["message"] or job["status"], style={"color": color, "marginTop": "8px"})]),
            True,
        )

    return html.Div([bar, status_text]), False
