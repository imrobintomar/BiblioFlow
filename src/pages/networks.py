import dash
from dash import html

dash.register_page(__name__, path="/networks", name="Networks")


def layout():
    return html.Div(
        [
            html.H3("Networks"),
            html.Div(
                className="panel-card",
                children=html.P(
                    "Citation, co-authorship, co-citation, and bibliographic coupling "
                    "networks are coming soon.",
                    className="coming-soon",
                ),
            ),
        ]
    )
