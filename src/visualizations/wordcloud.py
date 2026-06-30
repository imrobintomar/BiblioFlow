import math

import plotly.graph_objects as go

from visualizations.theme import apply_theme, color_for

WORDCLOUD_NOTE = (
    "Lightweight substitute for a true packed word cloud: words are placed "
    "along an Archimedean spiral (font size scaled by frequency rank), not "
    "collision-avoided rectangle packing. No extra `wordcloud`/PIL "
    "dependency needed -- pure Plotly."
)


def wordcloud_chart(words: list[str], weights: list[int], title: str | None = None) -> go.Figure:
    if not words:
        return apply_theme(go.Figure(), title=title)

    order = sorted(range(len(words)), key=lambda i: -weights[i])
    max_w = max(weights) or 1

    x, y, sizes, text, colors = [], [], [], [], []
    angle = 0.0
    radius = 0.0
    for rank, i in enumerate(order):
        x.append(radius * math.cos(angle))
        y.append(radius * math.sin(angle))
        sizes.append(10 + 28 * (weights[i] / max_w))
        text.append(words[i])
        colors.append(color_for(rank))
        angle += 0.7
        radius += 0.35

    fig = go.Figure(
        go.Scatter(
            x=x, y=y, mode="text", text=text,
            textfont=dict(size=sizes, color=colors),
        )
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return apply_theme(fig, title=title, height=420)
