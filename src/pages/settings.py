import dash
from dash import html

from config import CROSSREF_MAILTO, DB_PATH, PDF_DIR, SCOPUS_API_KEY

dash.register_page(__name__, path="/settings", name="Settings")


def _masked_key(key: str | None) -> str:
    if not key:
        return "Not configured"
    return f"{key[:4]}{'•' * 8}{key[-4:]}"


def layout():
    return html.Div(
        [
            html.H3("Settings"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("API Keys"),
                    html.P(f"Scopus API Key: {_masked_key(SCOPUS_API_KEY)}"),
                    html.P(f"CrossRef contact (polite pool): {CROSSREF_MAILTO}"),
                ],
            ),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Paths"),
                    html.P(f"PDF folder: {PDF_DIR}", style={"fontFamily": "monospace"}),
                    html.P(f"Database: {DB_PATH}", style={"fontFamily": "monospace"}),
                ],
            ),
            html.Div(
                className="panel-card",
                children=html.P(
                    "Subscription plans, AI model selection, cache management, and "
                    "notification preferences are coming soon.",
                    className="coming-soon",
                ),
            ),
        ]
    )
