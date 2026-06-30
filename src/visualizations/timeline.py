import plotly.graph_objects as go

from visualizations.theme import PRIMARY, apply_theme


def timeline_chart(labels: list[str], start: list, end: list, title: str | None = None) -> go.Figure:
    """Gantt-style timeline (e.g. each item's first-to-last active year) --
    rendered as horizontal bars with a base offset since Plotly's native
    px.timeline needs a pandas DataFrame, which this codebase avoids."""
    durations = [e - s for s, e in zip(start, end)]
    fig = go.Figure(
        go.Bar(
            base=start,
            x=durations,
            y=labels,
            orientation="h",
            marker_color=PRIMARY,
        )
    )
    return apply_theme(fig, title=title, height=max(280, 24 * len(labels)))
