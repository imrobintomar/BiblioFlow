import plotly.graph_objects as go

from visualizations.theme import PALETTE, apply_theme


def sunburst_chart(labels: list[str], values: list, parents: list[str], title: str | None = None) -> go.Figure:
    """For hierarchical compositions (e.g. Country > Institution > Paper)."""
    fig = go.Figure(
        go.Sunburst(
            labels=labels,
            values=values,
            parents=parents,
            marker=dict(colors=[PALETTE[i % len(PALETTE)] for i in range(len(labels))]),
        )
    )
    return apply_theme(fig, title=title, height=450)
