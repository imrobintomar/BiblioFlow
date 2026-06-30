import plotly.graph_objects as go

from visualizations.theme import color_for, apply_theme


def violin_chart(series: dict[str, list], title: str | None = None) -> go.Figure:
    fig = go.Figure()
    for i, (label, values) in enumerate(series.items()):
        fig.add_trace(go.Violin(y=values, name=label, line_color=color_for(i), box_visible=True, meanline_visible=True))
    return apply_theme(fig, title=title)
