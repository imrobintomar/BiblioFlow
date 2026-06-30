import dash
from dash import dcc, html

dash.register_page(__name__, path="/report", name="Report")


def layout():
    return html.Div(
        [
            html.H3("Report"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Coming soon"),
                    html.P(
                        "Biblioshiny's Report page generates an HTML/PDF summary report "
                        "across the whole analysis. Not yet built in BiblioFlow.",
                        className="coming-soon",
                    ),
                    html.P(
                        ["In the meantime, every chart/table panel across BiblioFlow has its own CSV download, and ",
                         dcc.Link("Library", href="/library", style={"color": "#052659"}),
                         " exports the full dataset as CSV/Excel."],
                        style={"color": "#5483B3"},
                    ),
                ],
            ),
        ]
    )
