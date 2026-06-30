import dash
from dash import html

dash.register_page(__name__, path="/tall-export", name="TALL Export")


def layout():
    return html.Div(
        [
            html.H3("TALL Export"),
            html.Div(
                className="panel-card",
                children=html.P(
                    "Exports the dataset in 'TALL' (one row per paper-author-keyword-etc. "
                    "combination) long format for external statistical tools. Not yet "
                    "built in BiblioFlow -- a future milestone.",
                    className="coming-soon",
                ),
            ),
        ]
    )
