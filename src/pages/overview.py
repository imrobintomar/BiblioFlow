import dash
import plotly.graph_objects as go
from dash import dcc, html

from components import biblio_panel
from config import WAREHOUSE_DB_PATH
from database.connection import get_connection
from engine import dataset, publications
from pages.analysis_shared import CHART_LAYOUT, bar_figure, stacked_bar_from_pivot
from repository.project_repository import ProjectRepository

dash.register_page(__name__, path="/overview", name="Overview")


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
                    html.H5("Main Information About Data"),
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
            children.append(html.P(text, style={"color": "#5483B3"}))
        if note is not None:
            children.append(html.P(note, style={"color": "#5483B3", "fontSize": "11px"}))
        return html.Div(className="panel-card", children=children)

    return html.Div(
        [
            biblio_panel(
                "ov-annual",
                "Annual Production",
                summary_rows=[
                    ("Timespan", f"{min(pub_data['by_year'].keys())} - {max(pub_data['by_year'].keys())}" if pub_data["by_year"] else "—"),
                    ("Total years", len(pub_data["by_year"])),
                    ("Total documents", sum(pub_data["by_year"].values())),
                    (
                        "Annual Growth Rate (CAGR)",
                        f"{pub_data['cagr_percent']}%" if pub_data["cagr_percent"] is not None else "n/a (need 2+ years)",
                    ),
                ],
                figure=bar_figure(list(pub_data["by_year"].keys()), list(pub_data["by_year"].values())),
                table_columns=["Year", "Documents"],
                table_rows=[{"Year": y, "Documents": c} for y, c in pub_data["by_year"].items()],
            ) if pub_data["by_year"] else html.Div("No dated papers yet.", className="coming-soon"),
            _panel(
                "Monthly Publications",
                fig=bar_figure(list(monthly["by_month"].keys()), list(monthly["by_month"].values())) if monthly["by_month"] else None,
                note="Scopus often supplies only year-01-01 when the exact month is unknown -- monthly data may look artificially clustered in January.",
            ) if monthly["by_month"] else html.Div("No month-level data available.", className="coming-soon"),
            _panel(
                "Quarterly Publications",
                fig=bar_figure(list(quarterly["by_quarter"].keys()), list(quarterly["by_quarter"].values())) if quarterly["by_quarter"] else None,
            ) if quarterly["by_quarter"] else html.Div("No quarter-level data available.", className="coming-soon"),
            _panel(
                "Publications per Decade",
                fig=bar_figure(list(decade["by_decade"].keys()), list(decade["by_decade"].values())),
            ),
            _panel(
                "Moving Average",
                fig=go.Figure(go.Scatter(x=ma["years"], y=ma["moving_average"], mode="lines+markers", line_color="#3F8F66")).update_layout(**CHART_LAYOUT),
            ),
            _panel("Forecast", text=forecast_text),
            _panel(
                "Cumulative Publications",
                fig=go.Figure(go.Scatter(x=list(cumulative["cumulative"].keys()), y=list(cumulative["cumulative"].values()), mode="lines+markers", fill="tozeroy", line_color="#052659")).update_layout(**CHART_LAYOUT),
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
            biblio_panel(
                "ov-growth-doctype",
                "Growth by Document Type",
                figure=stacked_bar_from_pivot(by_doctype),
                table_columns=["Year", "Document Type", "Count"],
                table_rows=[{"Year": y, "Document Type": g, "Count": c} for y, gd in by_doctype.items() for g, c in gd.items()],
            ) if by_doctype else html.Div("No document-type data available.", className="coming-soon"),
            _panel(
                "Growth by Country",
                fig=stacked_bar_from_pivot(by_country) if by_country else None,
            ) if by_country else html.Div("No country data available.", className="coming-soon"),
            _panel(
                "Growth by Institution (Top 8)",
                fig=stacked_bar_from_pivot(by_institution) if by_institution else None,
            ) if by_institution else html.Div("No institution data available.", className="coming-soon"),
            _panel(
                "Growth by Journal",
                fig=stacked_bar_from_pivot(by_journal) if by_journal else None,
            ) if by_journal else html.Div("No journal data available.", className="coming-soon"),
        ]
    )


def layout():
    with get_connection(WAREHOUSE_DB_PATH) as conn:
        project_id = ProjectRepository(conn).get_or_create_default("")
        overview_content = _overview_tab(conn, project_id)
        publication_content = _publication_tab(conn, project_id)

    return html.Div(
        [
            html.H3("Overview"),
            html.P(
                "Main Information about the dataset, plus Annual Production -- "
                "biblioshiny's classic landing view for a loaded corpus.",
                style={"color": "#5483B3"},
            ),
            overview_content,
            publication_content,
        ]
    )
