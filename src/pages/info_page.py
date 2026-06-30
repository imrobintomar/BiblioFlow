import dash
from dash import html

dash.register_page(__name__, path="/info", name="Info")


def layout():
    return html.Div(
        [
            html.H3("Info"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("BiblioFlow"),
                    html.P(
                        "A bibliometric analysis platform that takes downloaded PDFs and "
                        "turns them into structured, citation-ready records -- with a "
                        "local-first, biblioshiny-style dashboard and analysis engine on top.",
                        style={"color": "#5483B3"},
                    ),
                    html.P("Author: Robin Tomar (itsrobintomar@gmail.com)", style={"color": "#5483B3"}),
                ],
            ),
        ]
    )
