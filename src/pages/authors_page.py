import dash
from dash import dcc, html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import authors
from pages.analysis_shared import bar_figure, stacked_bar_from_pivot, top_n_control
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/authors", name="Authors")


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        top = authors.top_authors(conn, project_id, limit=top_n)
        timeline = authors.productivity_timeline(conn, project_id, limit=8)
        collab = authors.collaboration_stats(conn, project_id, limit=top_n)
        career = authors.career_stats(conn, project_id, limit=top_n)
        local_cit = authors.local_citations(conn, project_id)

    productivity_fig = bar_figure([a["author"] for a in top["authors"]], [a["papers"] for a in top["authors"]], orientation="h")

    panels = [
        biblio_panel(
            "auth-productivity",
            "Productivity (Full Counting vs Fractional)",
            summary_rows=[
                ("Total distinct authors", top["total_distinct_authors"]),
                ("Single most productive", top["authors"][0]["author"] if top["authors"] else "—"),
            ],
            figure=productivity_fig,
            table_columns=["Author", "Papers", "Fractional Papers", "First Pub", "Latest Pub", "Active Years"],
            table_rows=[
                {
                    "Author": a["author"], "Papers": a["papers"], "Fractional Papers": a["fractional_papers"],
                    "First Pub": a["first_publication"], "Latest Pub": a["latest_publication"], "Active Years": a["active_years"],
                }
                for a in top["authors"]
            ],
            note="Fractional counting credits each author 1/N of a paper with N authors -- "
            "contrasts with full counting (Papers), which credits every author a full unit.",
        ),
    ]

    if timeline:
        panels.append(
            biblio_panel(
                "auth-productivity-timeline", "Author Production over Time (Top 8)",
                figure=stacked_bar_from_pivot(timeline),
                table_columns=["Year", "Author", "Papers"],
                table_rows=[{"Year": y, "Author": a, "Papers": c} for y, ad in timeline.items() for a, c in ad.items()],
            )
        )

    panels.append(
        biblio_panel(
            "auth-citation-metrics",
            "Author Local Impact (H/G/M/i10/Contemporary-H/Normalized-H)",
            summary_rows=[("Total local-citation links (within this corpus)", local_cit["total_local_citation_links"])],
            table_columns=[
                "Author", "Total Citations (Global)", "Avg Citations", "H-index", "G-index",
                "i10-index", "M-index", "Contemporary H-index", "Normalized H-index", "Citation Velocity",
            ],
            table_rows=[
                {
                    "Author": a["author"], "Total Citations (Global)": a["total_citations"], "Avg Citations": a["avg_citations"],
                    "H-index": a["h_index"], "G-index": a["g_index"], "i10-index": a["i10_index"], "M-index": a["m_index"],
                    "Contemporary H-index": a["contemporary_h_index"], "Normalized H-index": a["normalized_h_index"],
                    "Citation Velocity": a["citation_velocity"],
                }
                for a in top["authors"]
            ],
            note="'Global' citations are from Scopus/OpenAlex (the whole literature). "
            "'Local' citations (within this imported corpus only) are tracked separately "
            "and are expected to be 0 for small corpora. Citation Half-Life is not "
            "computable with current data: it requires a citation-by-year timeline, but "
            "sources only give a single cumulative count.",
        )
    )

    panels.append(
        biblio_panel(
            "auth-collaboration", "Author Collaboration",
            table_columns=["Author", "Distinct Co-authors", "Countries Touched", "International Papers", "Domestic Papers"],
            table_rows=[
                {
                    "Author": c["author"], "Distinct Co-authors": c["distinct_co_authors"],
                    "Countries Touched": c["distinct_countries_touched"], "International Papers": c["international_papers"],
                    "Domestic Papers": c["domestic_papers"],
                }
                for c in collab["collaboration"]
            ],
            note="Country/institution collaboration is computed at the paper level, not "
            "true per-author attribution -- the schema links papers to institutions, not "
            "individual authors to their specific institution.",
        )
    )

    panels.append(
        biblio_panel(
            "auth-career", "Career (Peak Productivity Year, Citation History)",
            table_columns=["Author", "Peak Year", "Papers in Peak Year", "Citation History (by pub. year)"],
            table_rows=[
                {"Author": c["author"], "Peak Year": c["peak_year"], "Papers in Peak Year": c["peak_papers"], "Citation History (by pub. year)": str(c["citation_history"])}
                for c in career["career"]
            ],
            note="Citation History shows total citations of papers published in each "
            "year -- not citation accumulation over time, since sources only provide a "
            "cumulative snapshot count.",
        )
    )

    return html.Div(panels)


def layout():
    return html.Div(
        [
            html.H3("Authors"),
            top_n_control("authors-top-n", default=15, min_n=5, max_n=30, step=5),
            html.Div(id="authors-content", children=_render(15)),
        ]
    )


@dash.callback(Output("authors-content", "children"), Input("authors-top-n", "value"))
def update_authors(top_n):
    return _render(top_n)
