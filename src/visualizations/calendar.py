from visualizations.heatmap import heatmap_chart

CALENDAR_NOTE = (
    "True day-level GitHub-style calendar heatmaps need day-granularity "
    "publication dates, which no current source reliably provides (Scopus "
    "often gives only year-01-01). This renders a year x month density grid "
    "instead -- the finest granularity the data actually supports."
)


def calendar_heatmap(z: list[list], months: list, years: list, title: str | None = None):
    """Honest substitute for a true calendar heatmap -- see CALENDAR_NOTE."""
    return heatmap_chart(z, months, years, title=title)
