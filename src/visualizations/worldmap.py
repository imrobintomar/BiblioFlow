import plotly.graph_objects as go

from visualizations.theme import apply_theme


def choropleth_chart(countries: list[str], values: list, title: str | None = None) -> go.Figure:
    """Uses Plotly's native 'country names' location mode -- no ISO-code
    lookup needed. Countries whose name doesn't match Plotly's expected
    English name (e.g. minor spelling variants) silently won't render a
    shaded region; that's a real, visible gap rather than a crash."""
    fig = go.Figure(
        go.Choropleth(
            locations=countries,
            locationmode="country names",
            z=values,
            colorscale="Blues",
            colorbar_title="Papers",
        )
    )
    return apply_theme(
        fig,
        title=title,
        height=450,
        geo=dict(showframe=False, showcoastlines=False, projection_type="natural earth"),
    )
