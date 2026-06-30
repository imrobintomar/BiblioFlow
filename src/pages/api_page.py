import dash
from dash import dcc, html

dash.register_page(__name__, path="/api", name="API")


def layout():
    return html.Div(
        [
            html.H3("API"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Biblioshiny's 'API' page"),
                    html.P(
                        "In biblioshiny, this is a manual step to fetch metadata from an "
                        "external API (e.g. OpenAlex, PubMed) by query.",
                        style={"color": "#5483B3"},
                    ),
                    html.P(
                        "BiblioFlow does this automatically and per-paper: the enrichment "
                        "waterfall (CrossRef → OpenAlex → Semantic Scholar → PubMed → "
                        "Unpaywall → ROR) runs for every imported PDF as part of ",
                        style={"color": "#5483B3"},
                    ),
                    dcc.Link("Import", href="/import", style={"color": "#052659"}),
                    html.Span(" — no separate manual API step needed."),
                ],
            ),
        ]
    )
