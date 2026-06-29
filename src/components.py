from dash import dcc, html

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
