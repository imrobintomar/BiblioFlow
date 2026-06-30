import plotly.graph_objects as go

from visualizations.theme import apply_theme


def heatmap_chart(z: list[list], x_labels: list, y_labels: list, title: str | None = None) -> go.Figure:
    fig = go.Figure(go.Heatmap(z=z, x=x_labels, y=y_labels, colorscale="Blues"))
    return apply_theme(fig, title=title, height=max(280, 30 * len(y_labels)))
