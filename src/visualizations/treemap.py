import plotly.graph_objects as go

from visualizations.theme import PALETTE, apply_theme


def treemap_chart(labels: list[str], values: list, parents: list[str] | None = None, title: str | None = None) -> go.Figure:
    fig = go.Figure(
        go.Treemap(
            labels=labels,
            values=values,
            parents=parents or [""] * len(labels),
            marker=dict(colors=[PALETTE[i % len(PALETTE)] for i in range(len(labels))]),
            textinfo="label+value",
        )
    )
    return apply_theme(fig, title=title, height=420)
