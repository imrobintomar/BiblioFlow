import plotly.graph_objects as go

from visualizations.theme import PRIMARY, apply_theme


def histogram_chart(values: list, nbins: int | None = None, title: str | None = None) -> go.Figure:
    fig = go.Figure(go.Histogram(x=values, nbinsx=nbins, marker_color=PRIMARY))
    return apply_theme(fig, title=title)
