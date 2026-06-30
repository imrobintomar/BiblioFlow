import dash
from dash import dcc, html

dash.register_page(__name__, path="/data", name="Data")


def layout():
    return html.Div(
        [
            html.H3("Data"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Biblioshiny's 'Data' page"),
                    html.P(
                        "In biblioshiny, this is where you load a bibliographic collection "
                        "(sample dataset, Scopus/WoS/PubMed export file, etc.) before analysis.",
                        style={"color": "#5483B3"},
                    ),
                    html.P(
                        "BiblioFlow's equivalent today: ",
                        style={"color": "#5483B3"},
                    ),
                    dcc.Link("Import", href="/import", style={"color": "#052659"}),
                    html.Span(" (loads PDFs + runs the extraction/enrichment pipeline) and "),
                    dcc.Link("Library", href="/library", style={"color": "#052659"}),
                    html.Span(" (browse/filter/export the resulting dataset)."),
                ],
            ),
        ]
    )
