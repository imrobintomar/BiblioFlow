import dash
from dash import html

dash.register_page(__name__, path="/content-analysis", name="Content Analysis")


def layout():
    return html.Div(
        [
            html.H3("Content Analysis"),
            html.Div(
                className="panel-card",
                children=html.P(
                    "Biblioshiny's Content Analysis runs N-gram extraction and frequency "
                    "analysis over full-text PDF content. Not yet built in BiblioFlow -- "
                    "Docling already extracts full section text per paper "
                    "(see Paper Details), so the raw text is available; the analysis "
                    "layer on top of it isn't built yet.",
                    className="coming-soon",
                ),
            ),
        ]
    )
