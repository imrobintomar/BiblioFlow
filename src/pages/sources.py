import dash
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import documents, journals, languages, publishers
from pages.analysis_shared import CHART_LAYOUT, GROUP_COLORS, bar_figure, stacked_bar_from_pivot, top_n_control
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/sources", name="Sources")


def _journal_section(conn, project_id, limit):
    top = journals.top_journals(conn, project_id, limit=limit)
    core = journals.core_journals(conn, project_id)
    impact = journals.citation_impact(conn, project_id)
    growth = journals.journal_growth(conn, project_id)
    timeline = journals.journal_timeline(conn, project_id)
    oa = journals.open_access_journals(conn, project_id)
    pub_dist = journals.publisher_distribution(conn, project_id)

    if not top["journals"]:
        return [html.Div("No journal data available.", className="coming-soon")]

    top_fig = bar_figure([j["papers"] for j in top["journals"]], [j["journal"] for j in top["journals"]], orientation="h")

    panels = [
        biblio_panel(
            "jour-most-productive",
            "Most Productive Journals & Bradford Zones",
            summary_rows=[
                ("Total documents", sum(j["papers"] for j in top["journals"])),
                ("Distinct journals", len(top["journals"])),
                ("Core (Zone 1) journals", len(core["core"])),
            ],
            figure=top_fig,
            table_columns=["Journal", "Papers", "Avg Citations", "Bradford Zone"],
            table_rows=[
                {"Journal": j["journal"], "Papers": j["papers"], "Avg Citations": j["avg_citations"], "Bradford Zone": j["bradford_zone"]}
                for j in top["journals"]
            ],
            note="Bradford's Law: Zone 1 ('core') journals are the small set responsible "
            "for roughly the first third of the corpus's output.",
        ),
    ]
    if growth:
        panels.append(
            biblio_panel(
                "jour-growth", "Journal Growth / Source Dynamics",
                figure=stacked_bar_from_pivot(growth),
                table_columns=["Year", "Journal", "Papers"],
                table_rows=[{"Year": y, "Journal": g, "Papers": c} for y, gd in growth.items() for g, c in gd.items()],
            )
        )
    panels.append(
        biblio_panel(
            "jour-citation-impact", "Journal Citation Impact (Publications, Avg Citations, H-index)",
            table_columns=["Journal", "Papers", "Total Citations", "Avg Citations", "H-index"],
            table_rows=[
                {"Journal": k, "Papers": v["papers"], "Total Citations": v["total_citations"], "Avg Citations": v["avg_citations"], "H-index": v["h_index"]}
                for k, v in impact.items()
            ],
        )
    )
    panels.append(
        biblio_panel(
            "jour-timeline", "Journal Timeline & Lifespan",
            table_columns=["Journal", "First Year", "Last Year", "Lifespan (Years)"],
            table_rows=[
                {"Journal": k, "First Year": v["first_year"], "Last Year": v["last_year"], "Lifespan (Years)": v["lifespan_years"]}
                for k, v in timeline.items()
            ],
        )
    )
    panels.append(
        biblio_panel(
            "jour-open-access", "Open Access Journals & Publisher Distribution",
            table_columns=["Journal", "Total Papers", "Open Access %", "Publisher"],
            table_rows=[
                {"Journal": k, "Total Papers": v["total"], "Open Access %": v["open_pct"], "Publisher": pub_dist.get(k, "Unknown")}
                for k, v in oa.items()
            ],
        )
    )
    return panels


def _publisher_section(conn, project_id, limit):
    top = publishers.top_publishers(conn, project_id, limit=limit)
    growth = publishers.publisher_growth(conn, project_id)
    impact = publishers.citation_impact(conn, project_id)
    timeline = publishers.publisher_timeline(conn, project_id)
    oa_by_publisher = publishers.open_access_by_publisher(conn, project_id)

    if not top["publishers"]:
        return [html.Div("No publisher data available -- requires CrossRef's `publisher` field.", className="coming-soon")]

    top_fig = bar_figure([p["papers"] for p in top["publishers"]], [p["publisher"] for p in top["publishers"]], orientation="h")

    panels = [
        biblio_panel(
            "pub-top-publishers", "Top Publishers",
            summary_rows=[
                ("Total documents", sum(p["papers"] for p in top["publishers"])),
                ("Distinct publishers", len(top["publishers"])),
            ],
            figure=top_fig,
            table_columns=["Publisher", "Papers"],
            table_rows=top["publishers"],
        ),
    ]
    if growth:
        panels.append(
            biblio_panel(
                "pub-publisher-growth", "Publisher Growth",
                figure=stacked_bar_from_pivot(growth),
                table_columns=["Year", "Publisher", "Count"],
                table_rows=[{"Year": y, "Publisher": g, "Count": c} for y, gd in growth.items() for g, c in gd.items()],
            )
        )
    panels.append(
        biblio_panel(
            "pub-citation-impact", "Publisher Citation Impact (Publications, Avg Citations, H-index)",
            table_columns=["Publisher", "Papers", "Total Citations", "Avg Citations", "H-index"],
            table_rows=[
                {"Publisher": k, "Papers": v["papers"], "Total Citations": v["total_citations"], "Avg Citations": v["avg_citations"], "H-index": v["h_index"]}
                for k, v in impact.items()
            ],
        )
    )
    panels.append(
        biblio_panel(
            "pub-timeline", "Publisher Timeline",
            table_columns=["Publisher", "First Year", "Last Year"],
            table_rows=[{"Publisher": k, "First Year": v["first_year"], "Last Year": v["last_year"]} for k, v in timeline.items()],
        )
    )
    panels.append(
        biblio_panel(
            "pub-open-access", "Open Access by Publisher",
            table_columns=["Publisher", "Total Papers", "Open Access %"],
            table_rows=[{"Publisher": k, "Total Papers": v["total"], "Open Access %": v["open_pct"]} for k, v in oa_by_publisher.items()],
        )
    )
    return panels


def _document_section(conn, project_id):
    doctype_data = documents.document_type_distribution(conn, project_id)
    oa_data = documents.open_access_breakdown(conn, project_id)
    license_data = documents.license_distribution(conn, project_id)

    doctype_fig = go.Figure(go.Pie(labels=list(doctype_data["distribution"].keys()), values=list(doctype_data["distribution"].values()), hole=0.4, marker_colors=GROUP_COLORS))
    doctype_fig.update_layout(**CHART_LAYOUT)
    oa_fig = go.Figure(go.Pie(labels=list(oa_data["by_status"].keys()), values=list(oa_data["by_status"].values()), hole=0.4, marker_colors=GROUP_COLORS))
    oa_fig.update_layout(**CHART_LAYOUT)

    panels = [
        biblio_panel(
            "doc-types", "Document Types",
            summary_rows=[("Total documents", sum(doctype_data["distribution"].values())), ("Distinct types", len(doctype_data["distribution"]))],
            figure=doctype_fig,
            table_columns=["Document Type", "Count"],
            table_rows=[{"Document Type": k, "Count": v} for k, v in doctype_data["distribution"].items()],
            note="Sourced from CrossRef's `type` field, mapped to bibliometrix-style labels.",
        ),
        biblio_panel(
            "doc-open-access", "Open Access Distribution",
            summary_rows=[("Open Access %", f"{oa_data['open_pct']}%"), ("Closed Access %", f"{oa_data['closed_pct']}%")],
            figure=oa_fig if oa_data["by_status"] else None,
            table_columns=["OA Status", "Count"],
            table_rows=[{"OA Status": k, "Count": v} for k, v in oa_data["by_status"].items()],
        ) if oa_data["by_status"] else html.Div("No open access data available.", className="coming-soon"),
    ]
    if license_data["distribution"]:
        panels.append(
            biblio_panel(
                "doc-licenses", "License Distribution",
                table_columns=["License", "Count"],
                table_rows=[{"License": k, "Count": v} for k, v in license_data["distribution"].items()],
            )
        )
    else:
        panels.append(html.Div("No license data captured yet.", className="coming-soon"))
    return panels


def _language_section(conn, project_id):
    dist = languages.language_distribution(conn, project_id)
    growth = languages.growth_by_language(conn, project_id)
    cit_by_lang = languages.citations_by_language(conn, project_id)
    journals_by_lang = languages.journals_by_language(conn, project_id)
    country_lang = languages.country_vs_language(conn, project_id)

    dist_fig = go.Figure(go.Pie(labels=list(dist["distribution"].keys()), values=list(dist["distribution"].values()), hole=0.4, marker_colors=GROUP_COLORS))
    dist_fig.update_layout(**CHART_LAYOUT)

    panels = [
        biblio_panel(
            "lang-distribution", "Language Distribution",
            summary_rows=[("Total documents", sum(dist["distribution"].values())), ("Distinct languages", len(dist["distribution"]))],
            figure=dist_fig,
            table_columns=["Language", "Count"],
            table_rows=[{"Language": k, "Count": v} for k, v in dist["distribution"].items()],
            note="A corpus that's entirely (or mostly) one language is a real result, not a code limitation.",
        ),
    ]
    if growth:
        panels.append(
            biblio_panel(
                "lang-growth", "Growth by Language",
                figure=stacked_bar_from_pivot(growth),
                table_columns=["Year", "Language", "Count"],
                table_rows=[{"Year": y, "Language": g, "Count": c} for y, gd in growth.items() for g, c in gd.items()],
            )
        )
    panels.append(
        biblio_panel(
            "lang-citations", "Citations by Language",
            table_columns=["Language", "Papers", "Total Citations", "Avg Citations"],
            table_rows=[{"Language": k, "Papers": v["papers"], "Total Citations": v["total_citations"], "Avg Citations": v["avg_citations"]} for k, v in cit_by_lang.items()],
        )
    )
    panels.append(
        biblio_panel(
            "lang-journals", "Journals by Language",
            table_columns=["Language", "Distinct Journals"],
            table_rows=[{"Language": k, "Distinct Journals": v} for k, v in journals_by_lang.items()],
        ) if journals_by_lang else html.Div("No journal data available.", className="coming-soon")
    )
    panels.append(
        biblio_panel(
            "lang-country", "Country vs Language",
            figure=stacked_bar_from_pivot(country_lang) if country_lang else None,
            table_columns=["Country", "Language", "Count"],
            table_rows=[{"Country": c, "Language": g, "Count": n} for c, gd in country_lang.items() for g, n in gd.items()],
        ) if country_lang else html.Div("No country data available.", className="coming-soon")
    )
    return panels


def _render(top_n: int):
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        journal_panels = _journal_section(conn, project_id, top_n)
        publisher_panels = _publisher_section(conn, project_id, top_n)
        document_panels = _document_section(conn, project_id)
        language_panels = _language_section(conn, project_id)

    return dcc.Tabs(
        [
            dcc.Tab(label="Journals", children=journal_panels),
            dcc.Tab(label="Publishers", children=publisher_panels),
            dcc.Tab(label="Document Types", children=document_panels),
            dcc.Tab(label="Languages", children=language_panels),
        ]
    )


def layout():
    return html.Div(
        [
            html.H3("Sources"),
            top_n_control("sources-top-n", default=10, min_n=5, max_n=25, step=5),
            html.Div(id="sources-content", children=_render(10)),
        ]
    )


@dash.callback(Output("sources-content", "children"), Input("sources-top-n", "value"))
def update_sources(top_n):
    return _render(top_n)
