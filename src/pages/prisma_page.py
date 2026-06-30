import dash
from dash import html

dash.register_page(__name__, path="/prisma", name="PRISMA Diagram")


def layout():
    return html.Div(
        [
            html.H3("PRISMA Diagram"),
            html.Div(
                className="panel-card",
                children=html.P(
                    "Generates a PRISMA systematic-review flow diagram (records "
                    "identified/screened/excluded/included) from the dataset. Not yet "
                    "built in BiblioFlow -- a future milestone.",
                    className="coming-soon",
                ),
            ),
        ]
    )
