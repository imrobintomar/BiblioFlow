"""Shared chart helpers and Top-N control bar for the biblioshiny-style
section pages (overview, sources, authors, documents, conceptual_structure,
social_structure). Not a Dash page itself -- no dash.register_page call."""

import plotly.graph_objects as go
from dash import dcc, html

CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    margin=dict(l=30, r=20, t=10, b=30),
    height=280,
)

GROUP_COLORS = ["#052659", "#5483B3", "#D97706", "#040924", "#B3261E", "#7DA0CA", "#3F8F66", "#9FC8E8"]


def bar_figure(x, y, color="#052659", orientation="v"):
    if orientation == "h":
        fig = go.Figure(go.Bar(x=y, y=x, orientation="h", marker_color=color))
    else:
        fig = go.Figure(go.Bar(x=x, y=y, marker_color=color))
    fig.update_layout(**CHART_LAYOUT)
    return fig


def stacked_bar_from_pivot(pivot: dict) -> go.Figure:
    years = sorted(pivot.keys())
    groups = sorted({g for year_data in pivot.values() for g in year_data})
    fig = go.Figure()
    for i, group in enumerate(groups):
        fig.add_trace(
            go.Bar(
                name=group,
                x=years,
                y=[pivot.get(y, {}).get(group, 0) for y in years],
                marker_color=GROUP_COLORS[i % len(GROUP_COLORS)],
            )
        )
    fig.update_layout(barmode="stack", **CHART_LAYOUT)
    return fig


def top_n_control(control_id: str, default: int = 10, min_n: int = 5, max_n: int = 30, step: int = 5) -> html.Div:
    """Biblioshiny-style control bar: a single 'Top N items' slider that
    drives every rank-ordered panel on the page via one callback, rather
    than a separate control per chart."""
    marks = {n: str(n) for n in range(min_n, max_n + 1, step)}
    return html.Div(
        className="panel-card",
        children=[
            html.Label("Top N items", style={"fontWeight": "600", "color": "#040924"}),
            dcc.Slider(
                id=control_id,
                min=min_n,
                max=max_n,
                step=step,
                value=default,
                marks=marks,
                tooltip={"placement": "bottom"},
            ),
        ],
    )
