import plotly.graph_objects as go

from visualizations.theme import PALETTE, apply_theme


def sankey_chart(labels: list[str], source: list[int], target: list[int], value: list[int], title: str | None = None) -> go.Figure:
    """For flow/evolution analyses (topic evolution, theme transitions
    across periods) -- source/target are indices into labels."""
    fig = go.Figure(
        go.Sankey(
            node=dict(label=labels, color=[PALETTE[i % len(PALETTE)] for i in range(len(labels))]),
            link=dict(source=source, target=target, value=value),
        )
    )
    return apply_theme(fig, title=title, height=420)
