import plotly.graph_objects as go

from visualizations.theme import apply_theme, color_for


def area_chart(x: list, series: dict[str, list], stacked: bool = True, title: str | None = None) -> go.Figure:
    """series: {label: y_values}. Stacked area is the default -- appropriate
    for 'Growth' style analyses where parts contribute to a whole over time."""
    fig = go.Figure()
    stackgroup = "one" if stacked else None
    for i, (label, y) in enumerate(series.items()):
        fig.add_trace(
            go.Scatter(
                x=x, y=y, mode="lines", name=label, stackgroup=stackgroup,
                line=dict(color=color_for(i), width=1), fillcolor=color_for(i),
            )
        )
    if len(series) == 1:
        fig.update_layout(showlegend=False)
    return apply_theme(fig, title=title)
