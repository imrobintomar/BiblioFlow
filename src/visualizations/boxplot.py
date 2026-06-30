import plotly.graph_objects as go

from visualizations.theme import color_for, apply_theme


def boxplot_chart(series: dict[str, list], title: str | None = None) -> go.Figure:
    """series: {label: values}. One box per label -- e.g. citation
    percentile spread per journal, or per year."""
    fig = go.Figure()
    for i, (label, values) in enumerate(series.items()):
        fig.add_trace(go.Box(y=values, name=label, marker_color=color_for(i)))
    return apply_theme(fig, title=title)
