import plotly.graph_objects as go

from visualizations.theme import apply_theme, color_for


def line_chart(x: list, series: dict[str, list], title: str | None = None) -> go.Figure:
    """series: {label: y_values}. Single series for a plain trend line,
    multiple series for comparative trends on one axis."""
    fig = go.Figure()
    for i, (label, y) in enumerate(series.items()):
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=label, line=dict(color=color_for(i), width=2)))
    if len(series) == 1:
        fig.update_layout(showlegend=False)
    return apply_theme(fig, title=title)
