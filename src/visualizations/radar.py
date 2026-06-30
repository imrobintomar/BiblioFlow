import plotly.graph_objects as go

from visualizations.theme import color_for, apply_theme


def radar_chart(categories: list[str], series: dict[str, list], title: str | None = None) -> go.Figure:
    """series: {label: values}, one value per category -- e.g. comparing an
    author's H/G/M/i10 indices against the corpus average on one chart."""
    fig = go.Figure()
    for i, (label, values) in enumerate(series.items()):
        fig.add_trace(
            go.Scatterpolar(
                r=values + values[:1],
                theta=categories + categories[:1],
                fill="toself",
                name=label,
                line=dict(color=color_for(i)),
            )
        )
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)))
    return apply_theme(fig, title=title, height=400)
