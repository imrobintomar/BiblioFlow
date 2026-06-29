import dash
from dash import html

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import intellectual_structure as istruct
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/networks", name="Intellectual Structure")


def layout():
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        edges = istruct.reference_cocitation_edges(conn, project_id)
        historiograph = istruct.historiograph(conn, project_id)

    top_pairs = sorted(edges, key=lambda e: -e[2])[:30]

    panels = [
        biblio_panel(
            "intel-reference-cocitation",
            "Reference Co-citation (Most Co-Cited Reference Pairs)",
            summary_rows=[
                ("Total reference pairs co-cited within this corpus", len(edges)),
                ("Showing top", min(30, len(edges))),
            ],
            table_columns=["Reference A", "Reference B", "Co-citations"],
            table_rows=[{"Reference A": a, "Reference B": b, "Co-citations": w} for a, b, w in top_pairs],
            note="Two references are 'co-cited' when the same citing paper (within "
            "this corpus) lists both. The raw pair count is large mostly because two "
            "imported PDFs share the exact same DOI (duplicate import) and therefore "
            "their entire ~79-reference lists co-occur with each other -- not a "
            "meaningful cross-paper signal. A full graph isn't rendered here since the "
            "underlying network is too dense (20k+ pairs) to be visually useful; this "
            "table shows the strongest pairs only.",
        )
        if edges
        else html.Div("No reference co-citation data available.", className="coming-soon"),
        biblio_panel(
            "intel-historiograph",
            "Historiograph / Citation Tree (Local Citations, Chronological)",
            table_columns=["Title", "Year"],
            table_rows=historiograph["nodes_by_year"],
            note=historiograph["note"],
        )
        if historiograph["nodes_by_year"]
        else html.Div(historiograph["note"], className="coming-soon"),
        html.Div(
            className="panel-card",
            children=html.P(
                "Author Co-citation and Journal Co-citation networks are not "
                "implemented -- they require resolving each REFERENCED work's own "
                "authors/journal via an extra API call per reference (this corpus has "
                "400+ reference links total), which this milestone doesn't perform. "
                "A future milestone could batch-resolve references via OpenAlex by DOI.",
                className="coming-soon",
            ),
        ),
    ]

    return html.Div([html.H3("Intellectual Structure"), *panels])
