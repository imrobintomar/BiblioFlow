import dash
from dash import html

dash.register_page(__name__, path="/filters", name="Filters")


def layout():
    return html.Div(
        [
            html.H3("Filters"),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Coming soon"),
                    html.P(
                        "Biblioshiny's Filters page lets you restrict the active dataset "
                        "(by year range, document type, source, etc.) before running any "
                        "analysis, and includes a Reference Matching tool: fuzzy "
                        "deduplication of citation/reference strings (Jaro-Winkler "
                        "similarity, configurable threshold, manual merge UI).",
                        className="coming-soon",
                    ),
                    html.P(
                        "Reference Matching is directly relevant to a real, already-flagged "
                        "BiblioFlow gap: institution and reference names aren't deduplicated "
                        "across providers (e.g. 'Universiteit Leiden' vs 'Leiden University'). "
                        "Planned as the next concrete feature after this navigation update.",
                        className="coming-soon",
                    ),
                ],
            ),
        ]
    )
