import dash
import plotly.graph_objects as go
from dash import dcc, html

from components import biblio_panel, kpi_card, stat_group, status_badge
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import citations, dataset, journals
from repository.paper_repository import PaperRepository
from repository.project_repository import ProjectRepository
from services.event_service import EventService

dash.register_page(__name__, path="/", name="Dashboard")

CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    margin=dict(l=30, r=20, t=10, b=30),
    height=260,
)


def _trend_figure(by_year: dict) -> go.Figure:
    sorted_years = sorted(by_year.keys())
    fig = go.Figure(go.Bar(x=sorted_years, y=[by_year[y] for y in sorted_years], marker_color="#052659"))
    fig.update_layout(**CHART_LAYOUT)
    return fig


def _journals_figure(journal_rows: list[dict]) -> go.Figure:
    names = [j["journal"] for j in journal_rows]
    counts = [j["papers"] for j in journal_rows]
    fig = go.Figure(go.Bar(x=counts, y=names, orientation="h", marker_color="#3F8F66"))
    fig.update_layout(**CHART_LAYOUT)
    return fig


def _citation_histogram(top_cited: list[dict]) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=[p["title"][:30] + "…" if len(p["title"]) > 30 else p["title"] for p in top_cited],
            y=[p["citations"] for p in top_cited],
            marker_color="#D97706",
        )
    )
    fig.update_layout(**CHART_LAYOUT)
    return fig


def _recent_imports(papers: list[dict]) -> list[html.Div]:
    rows = []
    for p in papers[:8]:
        rows.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "padding": "8px 0",
                    "borderBottom": "1px solid #7DA0CA",
                },
                children=[
                    html.Span(p["filename"], style={"color": "#040924", "fontSize": "13px"}),
                    status_badge(p["status"]),
                ],
            )
        )
    if not rows:
        rows = [html.Div("No PDFs processed yet. Go to Import.", className="coming-soon")]
    return rows


def layout():
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        stats = dataset.get_module1_stats(conn, project_id)
        from engine import publications

        pub_data = publications.by_year(conn, project_id)
        cit_data = citations.get_distribution(conn, project_id)
        journal_data = journals.top_journals(conn, project_id, limit=5)
        papers = PaperRepository(conn).list_papers(project_id)
        project_row = next((p for p in ProjectRepository(conn).list_projects() if p["id"] == project_id), None)

    events = EventService().recent(project_id, limit=6)

    headline = [
        kpi_card("Documents", stats["total_papers"]),
        kpi_card("Authors", stats["total_authors"]),
        kpi_card("Citations", stats["total_citations"]),
        kpi_card("Metadata Quality", f"{stats['metadata_completeness']}%"),
    ]

    corpus_size_group = stat_group(
        "Corpus Size",
        [
            ("Total Documents", stats["total_papers"]),
            ("Total Authors", stats["total_authors"]),
            ("Total Journals (Sources)", stats["total_journals"]),
            ("Total Institutions", stats["total_institutions"]),
            ("Total Countries", stats["total_countries"]),
            ("Total Publishers", stats["total_publishers"]),
            ("Total References", stats["total_references"]),
            ("Total Keywords", stats["total_keywords"]),
            ("Total Citations", stats["total_citations"]),
        ],
    )

    averages_group = stat_group(
        "Averages & Collaboration",
        [
            ("Average Citations / Document", stats["avg_citations"]),
            ("Average Authors / Paper", stats["avg_authors"]),
            ("Average References / Paper", stats["avg_references"]),
            ("Average Keywords / Paper", stats["avg_keywords"]),
            ("Average Pages / Paper", stats["avg_pages"]),
            ("Average Word Count", stats["avg_word_count"]),
            ("Collaboration Index", stats["collaboration_index"]),
            ("Single-authored Papers", stats["single_authored"]),
            ("Multi-authored Papers", stats["multi_authored"]),
        ],
    )

    quality_group = stat_group(
        "Growth & Data Quality",
        [
            ("Open Access %", f"{stats['open_access_pct']}%"),
            ("Publication Span", stats["publication_span"]),
            ("Annual Growth Rate", f"{stats['annual_growth_rate']}%" if stats["annual_growth_rate"] is not None else None),
            ("CAGR", f"{stats['cagr']}%" if stats["cagr"] is not None else None),
            ("Duplication Rate", f"{stats['duplication_rate']}%"),
            ("Metadata Completeness", f"{stats['metadata_completeness']}%"),
            ("Metadata Confidence", f"{stats['metadata_confidence']}%" if stats["metadata_confidence"] else None),
        ],
    )

    source_group = stat_group(
        "Data Source Distribution",
        [(source.replace("_", " ").title(), count) for source, count in stats["source_distribution"].items()],
    )

    project_summary = stat_group(
        "Project Summary",
        [
            ("Project", project_row["name"] if project_row else "Default"),
            ("Papers", project_row["paper_count"] if project_row else stats["total_papers"]),
            ("Created", project_row["created_at"] if project_row else None),
        ],
    )

    return html.Div(
        [
            html.H3("Welcome, Robin"),
            html.Div(style={"display": "flex", "gap": "14px", "margin": "20px 0", "flexWrap": "wrap"}, children=headline),
            html.Div(
                style={"display": "flex", "gap": "20px"},
                children=[
                    html.Div(
                        style={"flex": 2},
                        children=[
                            html.Div(
                                style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
                                children=[
                                    html.Div(corpus_size_group, style={"flex": 1, "minWidth": "280px"}),
                                    html.Div(averages_group, style={"flex": 1, "minWidth": "280px"}),
                                    html.Div(quality_group, style={"flex": 1, "minWidth": "280px"}),
                                ],
                            ),
                            biblio_panel(
                                "dash-publication-trend",
                                "Publication Trend",
                                figure=_trend_figure(pub_data["by_year"]) if pub_data["by_year"] else None,
                                table_columns=["Year", "Documents"],
                                table_rows=[{"Year": y, "Documents": c} for y, c in pub_data["by_year"].items()],
                            ) if pub_data["by_year"] else html.Div(
                                className="panel-card",
                                children=[html.H5("Publication Trend"), html.P("No dated papers yet.", className="coming-soon")],
                            ),
                            biblio_panel(
                                "dash-top-journals",
                                "Top Journals",
                                figure=_journals_figure(journal_data["journals"]) if journal_data["journals"] else None,
                                table_columns=["Journal", "Papers"],
                                table_rows=[{"Journal": j["journal"], "Papers": j["papers"]} for j in journal_data["journals"]],
                            ) if journal_data["journals"] else html.Div(
                                className="panel-card",
                                children=[html.H5("Top Journals"), html.P("No journal data yet.", className="coming-soon")],
                            ),
                            biblio_panel(
                                "dash-citation-distribution",
                                "Citation Distribution (Top Cited)",
                                figure=_citation_histogram(cit_data["top_cited"]) if cit_data["top_cited"] else None,
                                table_columns=["Title", "Citations"],
                                table_rows=[{"Title": p["title"], "Citations": p["citations"]} for p in cit_data["top_cited"]],
                            ) if cit_data["top_cited"] else html.Div(
                                className="panel-card",
                                children=[html.H5("Citation Distribution (Top Cited)"), html.P("No citation data yet.", className="coming-soon")],
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": 1},
                        children=[
                            project_summary,
                            source_group,
                            html.Div(
                                className="panel-card",
                                children=[html.H5("Recent Imports"), *_recent_imports(papers)],
                            ),
                            html.Div(
                                className="panel-card",
                                children=[
                                    html.H5("Recent Activity"),
                                    *(
                                        [
                                            html.P(
                                                f"{e['timestamp']} — {e['type']}: {e['message']}",
                                                style={"color": "#5483B3", "fontSize": "12px"},
                                            )
                                            for e in events
                                        ]
                                        or [html.P("No activity yet.", className="coming-soon")]
                                    ),
                                ],
                            ),
                            html.Div(
                                className="panel-card",
                                children=[
                                    html.H5("Quick Actions"),
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column", "gap": "8px"},
                                        children=[
                                            dcc.Link("Import PDFs", href="/import", className="btn btn-outline-light btn-sm"),
                                            dcc.Link("New Project", href="/projects", className="btn btn-outline-light btn-sm"),
                                            dcc.Link("View Analysis", href="/analysis", className="btn btn-outline-light btn-sm"),
                                            dcc.Link("Library / Export", href="/library", className="btn btn-outline-light btn-sm"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )
