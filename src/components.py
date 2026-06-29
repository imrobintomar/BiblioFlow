from dash import dcc, html

from utils import export_cache

# Minimal Plotly mode bar -- keeps the PNG download (camera) button, drops
# the rest, consistent with biblioshiny's per-panel "download image" action.
CHART_DOWNLOAD_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
        "autoScale2d", "resetScale2d", "hoverClosestCartesian",
        "hoverCompareCartesian", "toggleSpikelines",
    ],
}

NAV_ITEMS = [
    ("Dashboard", "/", False),
    ("Projects", "/projects", False),
    ("Library", "/library", False),
    ("Import", "/import", False),
    ("Analysis", "/analysis", False),
    ("Networks", "/networks", True),
    ("AI", "/ai", True),
    ("Reports & Export", "/reports", True),
    ("Settings", "/settings", False),
]


def build_topbar() -> html.Div:
    return html.Div(
        className="topbar",
        children=[
            html.Span("BiblioFlow", className="logo"),
            dcc.Input(
                id="global-search",
                className="search-input",
                placeholder="Search papers, authors, DOI, journals...",
                type="text",
            ),
            html.Div(className="topbar-spacer"),
            html.Span("\U0001F514", className="topbar-icon", title="Notifications"),
            html.Span("Robin Tomar", style={"fontSize": "14px"}),
            html.Span("⚙", className="topbar-icon", title="Settings"),
        ],
    )


def build_sidebar() -> html.Div:
    links = []
    for label, path, soon in NAV_ITEMS:
        children = [label]
        if soon:
            children.append(html.Span("SOON", className="nav-soon-badge"))
        links.append(
            dcc.Link(children, href=path, className="nav-link", id={"type": "nav-link", "path": path})
        )
    return html.Div(className="sidebar", children=links)


def build_status_footer(status: dict) -> html.Div:
    def dot(connected: bool, label: str):
        cls = "status-dot connected" if connected else "status-dot disconnected"
        return html.Span([html.Span(className=cls), label])

    return html.Div(
        className="status-footer",
        children=[
            html.Span("BiblioFlow v0.1"),
            dot(status.get("sqlite", False), "SQLite"),
            dot(status.get("crossref", False), "CrossRef"),
            dot(status.get("scopus", False), "Scopus"),
        ],
    )


def kpi_card(label: str, value) -> html.Div:
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(label, className="kpi-label"),
            html.Div(f"{value:,}" if isinstance(value, int) else value, className="kpi-value"),
        ],
    )


def stat_row(label: str, value) -> html.Div:
    if value is None:
        display = "—"
    elif isinstance(value, float):
        display = f"{value:,.2f}"
    elif isinstance(value, int):
        display = f"{value:,}"
    else:
        display = str(value)
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "padding": "5px 0",
            "borderBottom": "1px solid #C8D9E6",
            "fontSize": "13px",
        },
        children=[html.Span(label, style={"color": "#6E8898"}), html.Span(display)],
    )


def stat_group(title: str, rows: list[tuple]) -> html.Div:
    return html.Div(
        className="panel-card",
        children=[html.H5(title), *[stat_row(label, value) for label, value in rows]],
    )


def _mini_table(columns: list[str], rows: list[dict], max_rows: int = 50) -> html.Table:
    return html.Table(
        style={"width": "100%", "fontSize": "12px", "borderCollapse": "collapse"},
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            c,
                            style={
                                "textAlign": "left",
                                "borderBottom": "2px solid #C8D9E6",
                                "padding": "4px 6px",
                                "color": "#2F4156",
                            },
                        )
                        for c in columns
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(
                                row.get(c, ""),
                                style={"padding": "4px 6px", "borderBottom": "1px solid #C8D9E6"},
                            )
                            for c in columns
                        ]
                    )
                    for row in rows[:max_rows]
                ]
            ),
        ],
    )


def biblio_panel(
    panel_id: str,
    title: str,
    summary_rows: list[tuple] | None = None,
    figure=None,
    table_columns: list[str] | None = None,
    table_rows: list[dict] | None = None,
    note: str | None = None,
) -> html.Div:
    """Biblioshiny-style result panel: a 'Main Information' summary block,
    then chart + its underlying data table side-by-side, with a CSV download
    for the table and a PNG download built into the chart's mode bar."""
    has_table = bool(table_columns and table_rows)
    if has_table:
        export_cache.register(panel_id, table_columns, table_rows)

    children = [html.H5(title)]

    if summary_rows:
        children.append(
            html.Div(
                style={"marginBottom": "14px"},
                children=[
                    html.Div(
                        "MAIN INFORMATION",
                        style={
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "color": "#6E8898",
                            "letterSpacing": "0.05em",
                            "marginBottom": "6px",
                        },
                    ),
                    *[stat_row(label, value) for label, value in summary_rows],
                ],
            )
        )

    if figure is not None and has_table:
        children.append(
            html.Div(
                style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
                children=[
                    html.Div(
                        dcc.Graph(figure=figure, config=CHART_DOWNLOAD_CONFIG),
                        style={"flex": 1, "minWidth": "320px"},
                    ),
                    html.Div(
                        _mini_table(table_columns, table_rows),
                        style={"flex": 1, "minWidth": "280px", "maxHeight": "320px", "overflowY": "auto"},
                    ),
                ],
            )
        )
    elif figure is not None:
        children.append(dcc.Graph(figure=figure, config=CHART_DOWNLOAD_CONFIG))
    elif has_table:
        children.append(_mini_table(table_columns, table_rows))

    if has_table:
        children.append(
            html.A(
                "Download CSV",
                href=f"/export/panel.csv?panel={panel_id}",
                className="btn btn-outline-light btn-sm",
                style={"marginTop": "10px", "display": "inline-block"},
            )
        )

    if note:
        children.append(html.P(note, style={"color": "#6E8898", "fontSize": "11px", "marginTop": "8px"}))

    return html.Div(className="panel-card", children=children)


STATUS_BADGE_MAP = {
    "scopus_fetched": ("done", "Scopus fetched"),
    "verified": ("done", "Verified"),
    "needs_review": ("review", "Needs review"),
    "verify_failed": ("failed", "CrossRef failed"),
    "extract_failed": ("failed", "No DOI found"),
    "scopus_failed": ("review", "Scopus not found"),
    "pending": ("pending", "Pending"),
}


def status_badge(status: str) -> html.Span:
    cls, label = STATUS_BADGE_MAP.get(status, ("pending", status))
    return html.Span(label, className=f"badge-status {cls}")
