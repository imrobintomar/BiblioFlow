import dash
from dash import dcc, html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import authors, countries, institutions, publications
from pages.analysis_shared import stacked_bar_from_pivot, top_n_control
from repository.project_repository import ProjectRepository
from visualizations.bubble import bubble_chart
from visualizations.worldmap import choropleth_chart

dash.register_page(__name__, path="/authors", name="Authors")


def _author_section(conn, project_id, top_n):
    top = authors.top_authors(conn, project_id, limit=top_n)
    timeline = authors.productivity_timeline(conn, project_id, limit=8)
    collab = authors.collaboration_stats(conn, project_id, limit=top_n)
    career = authors.career_stats(conn, project_id, limit=top_n)
    local_cit = authors.local_citations(conn, project_id)

    productivity_fig = bubble_chart(
        labels=[a["author"] for a in top["authors"]],
        x=[a["papers"] for a in top["authors"]],
        y=[a["total_citations"] for a in top["authors"]],
        size=[a["h_index"] + 1 for a in top["authors"]],
        title="Papers vs Citations (bubble size = H-index)",
        x_title="Papers",
        y_title="Total Citations",
    )

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

    return panels


def _institution_section(conn, project_id, top_n):
    top = institutions.top_institutions(conn, project_id, limit=top_n)
    growth = institutions.institution_growth(conn, project_id, limit=min(top_n, 8))
    impact = institutions.citation_impact(conn, project_id)
    collab = institutions.collaboration(conn, project_id, limit=top_n)
    researchers = institutions.top_researchers(conn, project_id, limit=top_n)
    timeline = institutions.publication_timeline(conn, project_id)
    country_dist = institutions.country_distribution(conn, project_id)
    funding_dist = institutions.funding_distribution(conn, project_id, limit=top_n)

    if not top["institutions"]:
        return [html.Div("No institution data available.", className="coming-soon")]

    top_fig = bubble_chart(
        labels=[i["institution"] for i in top["institutions"]],
        x=[i["papers"] for i in top["institutions"]],
        y=[impact.get(i["institution"], {}).get("total_citations", 0) for i in top["institutions"]],
        size=[impact.get(i["institution"], {}).get("h_index", 0) + 1 for i in top["institutions"]],
        title="Papers vs Citations (bubble size = H-index)",
        x_title="Papers",
        y_title="Total Citations",
    )

    panels = [
        biblio_panel(
            "inst-most-productive", "Most Productive Institutions",
            summary_rows=[
                ("Total documents", sum(i["papers"] for i in top["institutions"])),
                ("Distinct institutions", len(top["institutions"])),
            ],
            figure=top_fig,
            table_columns=["Institution", "Papers"],
            table_rows=top["institutions"],
        ),
    ]

    if growth:
        panels.append(
            biblio_panel(
                "inst-growth", "Institution Growth",
                figure=stacked_bar_from_pivot(growth),
                table_columns=["Year", "Institution", "Papers"],
                table_rows=[{"Year": y, "Institution": g, "Papers": c} for y, gd in growth.items() for g, c in gd.items()],
            )
        )

    panels.append(
        biblio_panel(
            "inst-citation-impact", "Institutional Citation Impact (incl. Institutional H-index)",
            table_columns=["Institution", "Papers", "Total Citations", "Avg Citations", "H-index"],
            table_rows=[
                {"Institution": k, "Papers": v["papers"], "Total Citations": v["total_citations"], "Avg Citations": v["avg_citations"], "H-index": v["h_index"]}
                for k, v in impact.items()
            ],
        )
    )

    panels.append(
        biblio_panel(
            "inst-collaboration", "Institution Collaboration (Network Edge Counts)",
            table_columns=["Institution", "Co-occurring Institutions"],
            table_rows=collab["collaboration"],
            note="Counts of distinct institutions appearing on a shared paper -- the "
            "underlying edge list for an institution network. Rendering this as an "
            "actual graph is a future Network Analysis milestone.",
        )
    )

    panels.append(
        biblio_panel(
            "inst-researchers", "Top Researchers per Institution",
            table_columns=["Institution", "Distinct Researchers"],
            table_rows=researchers["researchers"],
            note="Paper-level proxy: counts authors on any paper linked to this "
            "institution, not true author-to-institution attribution -- the schema "
            "links papers (not individual authors) to institutions.",
        )
    )

    panels.append(
        biblio_panel(
            "inst-timeline", "Publication Timeline",
            table_columns=["Institution", "First Year", "Last Year"],
            table_rows=[{"Institution": k, "First Year": v["first_year"], "Last Year": v["last_year"]} for k, v in timeline.items()],
        )
    )

    panels.append(
        biblio_panel(
            "inst-country", "Country Distribution",
            table_columns=["Institution", "Country"],
            table_rows=[{"Institution": k, "Country": v} for k, v in country_dist.items()],
        )
    )

    panels.append(
        biblio_panel(
            "inst-funding", "Funding Distribution",
            table_columns=["Institution", "Funders"],
            table_rows=[{"Institution": f["institution"], "Funders": ", ".join(f["funders"])} for f in funding_dist["funding"]],
            note="Paper-level proxy: funders on any paper linked to this institution -- "
            "the schema has no direct institution-to-funder edge.",
        ) if funding_dist["funding"] else html.Div("No funding data linked to institutions yet.", className="coming-soon")
    )

    return panels


def _country_section(conn, project_id, top_n):
    """Matches biblioshiny's Authors sub-items: Countries' Scientific
    Production, Countries' Production over Time, Most Cited Countries.
    ('Corresponding Author's Countries' isn't implemented -- we don't flag
    a corresponding author, so country counts here are per all affiliations.)"""
    top = countries.top_countries(conn, project_id, limit=top_n)
    most_cited = countries.most_cited_countries(conn, project_id, limit=top_n)
    growth = publications.growth_by_country(conn, project_id)

    if not top["countries"]:
        return [html.Div(top["note"], className="coming-soon")]

    fig = choropleth_chart([c["country"] for c in top["countries"]], [c["papers"] for c in top["countries"]], title="Countries' Scientific Production")

    panels = [
        biblio_panel(
            "auth-country-production", "Countries' Scientific Production",
            summary_rows=[("Distinct countries", len(top["countries"]))],
            figure=fig,
            table_columns=["Country", "Papers"],
            table_rows=[{"Country": c["country"], "Papers": c["papers"]} for c in top["countries"]],
            note="Per-paper affiliation country, not corresponding-author-only "
            "(BiblioFlow doesn't currently flag which author corresponds).",
        ),
    ]

    if growth:
        panels.append(
            biblio_panel(
                "auth-country-over-time", "Countries' Production over Time",
                figure=stacked_bar_from_pivot(growth),
                table_columns=["Year", "Country", "Count"],
                table_rows=[{"Year": y, "Country": g, "Count": c} for y, gd in growth.items() for g, c in gd.items()],
            )
        )

    panels.append(
        biblio_panel(
            "auth-most-cited-countries", "Most Cited Countries",
            table_columns=["Country", "Total Citations"],
            table_rows=[{"Country": c["country"], "Total Citations": c["total_citations"]} for c in most_cited["countries"]],
        )
    )

    return panels


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        author_panels = _author_section(conn, project_id, top_n)
        institution_panels = _institution_section(conn, project_id, top_n)
        country_panels = _country_section(conn, project_id, top_n)

    return dcc.Tabs(
        [
            dcc.Tab(label="Authors", children=author_panels),
            dcc.Tab(label="Affiliations", children=institution_panels),
            dcc.Tab(label="Countries", children=country_panels),
        ]
    )


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
