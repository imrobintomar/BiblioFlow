import dash
from dash import dcc, html

dash.register_page(__name__, path="/ai", name="AI")


def layout():
    return html.Div(
        [
            html.H3("AI Assistant"),
            html.Div(
                className="panel-card",
                children=[
                    dcc.Input(
                        placeholder="Ask BiblioFlow AI (coming soon)...",
                        className="search-input",
                        style={"width": "100%"},
                        disabled=True,
                    ),
                    html.P(
                        "AI chat, literature review generation, research gap detection, "
                        "and semantic search are coming soon.",
                        className="coming-soon",
                        style={"marginTop": "16px"},
                    ),
                ],
            ),
        ]
    )
