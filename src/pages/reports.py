import dash
from dash import html

dash.register_page(__name__, path="/reports", name="Reports & Export")


def layout():
    return html.Div(
        [
            html.H3("Reports & Export"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Already available from the CLI pipeline"),
                    html.P(
                        "results.json, results.csv, results.bib, and a "
                        "bibliometrix-compatible Scopus CSV are written to out/ "
                        "after each pipeline run.",
                        style={"color": "#6E8898"},
                    ),
                ],
            ),
            html.Div(
                className="panel-card",
                children=html.P(
                    "In-app HTML/PDF/Word/PowerPoint report generation and GraphML/GEXF "
                    "network exports are coming soon.",
                    className="coming-soon",
                ),
            ),
        ]
    )
