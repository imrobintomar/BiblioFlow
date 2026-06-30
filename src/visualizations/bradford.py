import plotly.graph_objects as go

from visualizations.theme import BRAND_DARK, apply_theme

CORE_ZONE_FILL = "rgba(125, 160, 202, 0.25)"  # translucent LIGHT


def bradford_curve(sources: list[str], cumulative_papers: list[int], core_count: int, title: str | None = None) -> go.Figure:
    """Real Bradford's Law rank-frequency curve: sources ranked by
    productivity (descending), cumulative paper count plotted against
    log(rank), with the 'core' zone (the small set of sources responsible
    for roughly a third of output) shaded -- matches biblioshiny's
    'Core Sources by Bradford's Law' chart, not just a zone-labeled bar."""
    n = len(sources)
    ranks = list(range(1, n + 1))

    fig = go.Figure()

    if core_count > 0:
        fig.add_shape(
            type="rect",
            x0=1, x1=core_count,
            y0=0, y1=max(cumulative_papers) if cumulative_papers else 1,
            fillcolor=CORE_ZONE_FILL,
            line=dict(width=0),
            layer="below",
        )
        fig.add_annotation(
            x=(1 + core_count) / 2, y=(max(cumulative_papers) if cumulative_papers else 1) * 0.6,
            text="Core<br>Sources", showarrow=False,
            font=dict(size=16, color=BRAND_DARK), opacity=0.6,
        )

    fig.add_trace(
        go.Scatter(
            x=ranks, y=cumulative_papers, mode="lines",
            line=dict(color=BRAND_DARK, width=2), showlegend=False,
        )
    )

    fig.update_xaxes(
        type="log",
        tickmode="array",
        tickvals=ranks,
        ticktext=sources,
        tickangle=-90,
        title="Source log(Rank)",
    )
    return apply_theme(fig, title=title, yaxis_title="Articles", height=420, margin=dict(l=40, r=20, t=30, b=160))
