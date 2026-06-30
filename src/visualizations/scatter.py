import plotly.graph_objects as go

from visualizations.theme import PRIMARY, apply_theme


def scatter_chart(x: list, y: list, labels: list[str] | None = None, size: list | None = None, color: list | None = None, title: str | None = None) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="markers" if not labels else "markers+text",
            text=labels,
            textposition="top center",
            marker=dict(size=size or 10, color=color or PRIMARY, opacity=0.75),
        )
    )
    return apply_theme(fig, title=title)
