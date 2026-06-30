import plotly.graph_objects as go

from visualizations.theme import LIGHT, PRIMARY, apply_theme

# Dark-to-light gradient by rank, matching biblioshiny's "Most Relevant X"
# convention -- highest value gets the darkest marker.
_GRADIENT = ["#040924", "#052659", "#0A3D7A", "#155A9C", "#2E78B8", "#5483B3", "#7DA0CA", "#9FC8E8"]


def _gradient_color(rank: int, total: int) -> str:
    if total <= 1:
        return _GRADIENT[0]
    idx = int(rank / max(1, total - 1) * (len(_GRADIENT) - 1))
    return _GRADIENT[idx]


def lollipop_chart(labels: list[str], values: list, title: str | None = None, x_title: str | None = None) -> go.Figure:
    """Stem + value-labeled bubble, color-graded dark-to-light by rank --
    biblioshiny's dominant style for ranked lists (Most Relevant
    Words/Sources/Authors, Most Cited Documents), more polished than a
    plain bar for this kind of single-metric ranking."""
    n = len(labels)
    colors = [_gradient_color(i, n) for i in range(n)]

    fig = go.Figure()
    for i, (label, value) in enumerate(zip(labels, values)):
        fig.add_trace(
            go.Scatter(
                x=[0, value], y=[label, label], mode="lines",
                line=dict(color=LIGHT, width=1.5), showlegend=False, hoverinfo="skip",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=values, y=labels, mode="markers+text",
            text=[str(v) for v in values],
            textposition="middle center",
            textfont=dict(size=10, color="#FFFFFF"),
            marker=dict(size=28, color=colors, line=dict(width=0)),
            showlegend=False,
        )
    )
    fig.update_yaxes(categoryorder="array", categoryarray=labels[::-1])
    return apply_theme(fig, title=title, xaxis_title=x_title, height=max(280, 36 * n))
