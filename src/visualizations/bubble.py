import plotly.graph_objects as go

from visualizations.theme import PRIMARY, apply_theme


def bubble_chart(
    labels: list[str], x: list, y: list, size: list, color: list | None = None, title: str | None = None,
    x_title: str | None = None, y_title: str | None = None,
) -> go.Figure:
    """Three-to-four-dimensional comparison (e.g. Authors: papers vs
    citations, bubble size = H-index) -- the guideline's choice for
    Authors/Institutions instead of a flat ranked bar."""
    max_size = max(size) if size and max(size) > 0 else 1
    scaled_size = [10 + 40 * (s / max_size) for s in size]

    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="markers+text",
            text=labels,
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(size=scaled_size, color=color or PRIMARY, opacity=0.75, line=dict(width=1, color="#FFFFFF")),
        )
    )
    return apply_theme(fig, title=title, height=420, xaxis_title=x_title, yaxis_title=y_title)
