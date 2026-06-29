import dash
import plotly.graph_objects as go
from dash import dcc, html

from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import citations, countries, dataset, funding, keywords, publications, references
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/analysis", name="Analysis")

SOON_TABS = [
    "Author Analysis",
    "Journal Analysis",
    "Institution Analysis",
]

CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    margin=dict(l=30, r=20, t=10, b=30),
    height=280,
)


def _overview_tab(conn, project_id):
    overview = dataset.get_overview(conn, project_id)
    completeness = overview.get("metadata_completeness", {})

    rows = [
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "padding": "6px 0"},
            children=[html.Span(k.title()), html.Span(f"{v}%")],
        )
        for k, v in completeness.items()
    ]

    return html.Div(
        [
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Dataset Overview"),
                    html.P(f"Total documents: {overview['total_papers']}"),
                    html.P(f"Average citations per paper: {overview['avg_citations']}"),
                    html.P(f"Average authors per paper: {overview['avg_authors']}"),
                ],
            ),
            html.Div(
                className="panel-card",
                children=[html.H5("Metadata Completeness by Field"), *rows],
            ),
        ]
    )


_GROUP_COLORS = ["#567C8D", "#3F8F66", "#D97706", "#2F4156", "#B3261E", "#8AAFC0", "#7FB89A", "#C8D9E6"]


def _bar_figure(x, y, color="#567C8D", orientation="v"):
    if orientation == "h":
        fig = go.Figure(go.Bar(x=y, y=x, orientation="h", marker_color=color))
    else:
        fig = go.Figure(go.Bar(x=x, y=y, marker_color=color))
    fig.update_layout(**CHART_LAYOUT)
    return fig


def _stacked_bar_from_pivot(pivot: dict) -> go.Figure:
    years = sorted(pivot.keys())
    groups = sorted({g for year_data in pivot.values() for g in year_data})
    fig = go.Figure()
    for i, group in enumerate(groups):
        fig.add_trace(
            go.Bar(
                name=group,
                x=years,
                y=[pivot.get(y, {}).get(group, 0) for y in years],
                marker_color=_GROUP_COLORS[i % len(_GROUP_COLORS)],
            )
        )
    fig.update_layout(barmode="stack", **CHART_LAYOUT)
    return fig


def _publication_tab(conn, project_id):
    pub_data = publications.by_year(conn, project_id)
    monthly = publications.by_month(conn, project_id)
    quarterly = publications.by_quarter(conn, project_id)
    decade = publications.by_decade(conn, project_id)
    ma = publications.moving_average(pub_data["by_year"])
    forecast = publications.forecast_next_period(pub_data["by_year"])
    cumulative = publications.cumulative(pub_data["by_year"])
    density = publications.density(conn, project_id)
    heat = publications.heatmap(conn, project_id)
    by_doctype = publications.growth_by_document_type(conn, project_id)
    by_country = publications.growth_by_country(conn, project_id)
    by_institution = publications.growth_by_institution(conn, project_id)
    by_journal = publications.growth_by_journal(conn, project_id)

    forecast_text = (
        f"Forecast for {forecast['forecast']['year']}: ~{forecast['forecast']['predicted_papers']} papers"
        if forecast["forecast"]
        else forecast["note"]
    )

    heatmap_fig = go.Figure(
        go.Heatmap(z=heat["matrix"], x=heat["months"], y=heat["years"], colorscale="Blues")
    )
    heatmap_fig.update_layout(**CHART_LAYOUT)

    def _panel(title, fig=None, text=None, note=None):
        children = [html.H5(title)]
        if fig is not None:
            children.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))
        if text is not None:
            children.append(html.P(text, style={"color": "#6E8898"}))
        if note is not None:
            children.append(html.P(note, style={"color": "#6E8898", "fontSize": "11px"}))
        return html.Div(className="panel-card", children=children)

    return html.Div(
        [
            _panel(
                "Annual Publications",
                fig=_bar_figure(list(pub_data["by_year"].keys()), list(pub_data["by_year"].values())),
                text=f"CAGR / Annual Growth Rate: {pub_data['cagr_percent']}%" if pub_data["cagr_percent"] is not None else "CAGR: n/a (need 2+ years)",
            ),
            _panel(
                "Monthly Publications",
                fig=_bar_figure(list(monthly["by_month"].keys()), list(monthly["by_month"].values())) if monthly["by_month"] else None,
                note="Scopus often supplies only year-01-01 when the exact month is unknown -- monthly data may look artificially clustered in January.",
            ) if monthly["by_month"] else html.Div("No month-level data available.", className="coming-soon"),
            _panel(
                "Quarterly Publications",
                fig=_bar_figure(list(quarterly["by_quarter"].keys()), list(quarterly["by_quarter"].values())) if quarterly["by_quarter"] else None,
            ) if quarterly["by_quarter"] else html.Div("No quarter-level data available.", className="coming-soon"),
            _panel(
                "Publications per Decade",
                fig=_bar_figure(list(decade["by_decade"].keys()), list(decade["by_decade"].values())),
            ),
            _panel(
                "Moving Average",
                fig=go.Figure(go.Scatter(x=ma["years"], y=ma["moving_average"], mode="lines+markers", line_color="#3F8F66")).update_layout(**CHART_LAYOUT),
            ),
            _panel("Forecast", text=forecast_text),
            _panel(
                "Cumulative Publications",
                fig=go.Figure(go.Scatter(x=list(cumulative["cumulative"].keys()), y=list(cumulative["cumulative"].values()), mode="lines+markers", fill="tozeroy", line_color="#567C8D")).update_layout(**CHART_LAYOUT),
            ),
            _panel(
                "Publication Density / Life Cycle",
                text=f"{density['papers_per_year']} papers/year over a {density['span_years']}-year span",
            ),
            _panel(
                "Publication Heatmap / Calendar (Year x Month)",
                fig=heatmap_fig,
                note="Month-level granularity is the floor available from current sources; true day-level publication dates aren't reliably captured by any source.",
            ),
            _panel(
                "Growth by Document Type",
                fig=_stacked_bar_from_pivot(by_doctype) if by_doctype else None,
            ) if by_doctype else html.Div("No document-type data available.", className="coming-soon"),
            _panel(
                "Growth by Country",
                fig=_stacked_bar_from_pivot(by_country) if by_country else None,
            ) if by_country else html.Div("No country data available.", className="coming-soon"),
            _panel(
                "Growth by Institution (Top 8)",
                fig=_stacked_bar_from_pivot(by_institution) if by_institution else None,
            ) if by_institution else html.Div("No institution data available.", className="coming-soon"),
            _panel(
                "Growth by Journal",
                fig=_stacked_bar_from_pivot(by_journal) if by_journal else None,
            ) if by_journal else html.Div("No journal data available.", className="coming-soon"),
        ]
    )


def _citation_tab(conn, project_id):
    cit_data = citations.get_distribution(conn, project_id)

    hist_fig = go.Figure(
        go.Bar(
            x=[p["title"][:30] + "…" if len(p["title"]) > 30 else p["title"] for p in cit_data["top_cited"]],
            y=[p["citations"] for p in cit_data["top_cited"]],
            marker_color="#D97706",
        )
    )
    hist_fig.update_layout(**CHART_LAYOUT)

    percentile_rows = [
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "padding": "6px 0"},
            children=[html.Span(k.upper()), html.Span(str(v))],
        )
        for k, v in cit_data["percentiles"].items()
    ]

    return html.Div(
        [
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Citation Summary"),
                    html.P(f"Total citations: {cit_data['total_citations']}"),
                    html.P(f"Average: {cit_data['average']}"),
                    html.P(f"Median: {cit_data['median']}"),
                ],
            ),
            html.Div(className="panel-card", children=[html.H5("Citation Percentiles"), *percentile_rows]),
            html.Div(
                className="panel-card",
                children=[
                    html.H5("Top Cited Papers"),
                    dcc.Graph(figure=hist_fig, config={"displayModeBar": False})
                    if cit_data["top_cited"]
                    else html.P("No citation data yet.", className="coming-soon"),
                ],
            ),
        ]
    )


def _country_tab(conn, project_id):
    data = countries.top_countries(conn, project_id)
    if not data["countries"]:
        return html.Div(data["note"], className="coming-soon")

    fig = go.Figure(
        go.Bar(
            x=[c["papers"] for c in data["countries"]],
            y=[c["country"] for c in data["countries"]],
            orientation="h",
            marker_color="#567C8D",
        )
    )
    fig.update_layout(**CHART_LAYOUT)
    return html.Div(
        className="panel-card",
        children=[html.H5("Papers by Country"), dcc.Graph(figure=fig, config={"displayModeBar": False})],
    )


def _keyword_tab(conn, project_id):
    data = keywords.top_keywords(conn, project_id)
    if not data["keywords"]:
        return html.Div(data["note"], className="coming-soon")

    fig = go.Figure(
        go.Bar(
            x=[k["papers"] for k in data["keywords"][:20]],
            y=[k["keyword"] for k in data["keywords"][:20]],
            orientation="h",
            marker_color="#3F8F66",
        )
    )
    fig.update_layout(**{**CHART_LAYOUT, "height": 500})
    return html.Div(
        [
            html.Div(
                className="panel-card",
                children=[html.H5("Top Keywords / Concepts"), dcc.Graph(figure=fig, config={"displayModeBar": False})],
            ),
            html.P(
                "Sourced from PubMed MeSH terms, OpenAlex concepts, or PDF-extracted "
                "keyword lines, in that priority order.",
                style={"color": "#6E8898", "fontSize": "12px"},
            ),
        ]
    )


def _reference_tab(conn, project_id):
    data = references.most_cited_references(conn, project_id)
    rows = conn.execute(
        "SELECT COUNT(*) AS c FROM paper_references JOIN papers ON papers.id = paper_references.paper_id WHERE papers.project_id = ?",
        (project_id,),
    ).fetchone()
    total_refs = rows["c"] if rows else 0

    return html.Div(
        className="panel-card",
        children=[
            html.H5("Reference Analysis"),
            html.P(f"Total reference links captured: {total_refs}"),
            html.P(
                "Most references are sourced from OpenAlex/Semantic Scholar (not yet "
                "resolved to a shared DOI namespace across both, so 'most cited within "
                "this corpus' under-counts until that resolution is added).",
                style={"color": "#6E8898", "fontSize": "12px"},
            ),
        ],
    )


def _funding_tab(conn, project_id):
    data = funding.top_funders(conn, project_id)
    if not data["funders"]:
        return html.Div("No funders detected yet.", className="coming-soon")

    rows = [
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "padding": "6px 0"},
            children=[html.Span(f["funder"]), html.Span(str(f["papers"]))],
        )
        for f in data["funders"]
    ]
    return html.Div(
        [
            html.Div(className="panel-card", children=[html.H5("Top Funders"), *rows]),
            html.P(data["note"], style={"color": "#6E8898", "fontSize": "12px"}),
        ]
    )


def layout():
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        overview_content = _overview_tab(conn, project_id)
        publication_content = _publication_tab(conn, project_id)
        citation_content = _citation_tab(conn, project_id)
        country_content = _country_tab(conn, project_id)
        keyword_content = _keyword_tab(conn, project_id)
        reference_content = _reference_tab(conn, project_id)
        funding_content = _funding_tab(conn, project_id)

    return html.Div(
        [
            html.H3("Analysis"),
            dcc.Tabs(
                [
                    dcc.Tab(label="Overview", children=[overview_content]),
                    dcc.Tab(label="Publication Analysis", children=[publication_content]),
                    dcc.Tab(label="Citation Analysis", children=[citation_content]),
                    dcc.Tab(label="Country Analysis", children=[country_content]),
                    dcc.Tab(label="Keyword Analysis", children=[keyword_content]),
                    dcc.Tab(label="Reference Analysis", children=[reference_content]),
                    dcc.Tab(label="Funding Analysis", children=[funding_content]),
                    *[
                        dcc.Tab(
                            label=tab,
                            children=[html.Div(f"{tab} — coming soon.", className="coming-soon")],
                        )
                        for tab in SOON_TABS
                    ],
                ]
            ),
        ]
    )
