"""Shared visual design system for every chart in visualizations/. Apply via
_apply_theme() at the end of each chart-building function so every chart in
BiblioFlow shares consistent layout, spacing, typography, and color usage."""

import plotly.graph_objects as go

BRAND_DARK = "#040924"
PRIMARY = "#052659"
SECONDARY = "#5483B3"
LIGHT = "#7DA0CA"
BACKGROUND_ACCENT = "#C1E8FF"

SUCCESS = "#3F8F66"
WARNING = "#D97706"
DANGER = "#B3261E"

# Categorical palette for multi-series charts (bubble color groups, treemap
# branches, network communities, etc.) -- cycles through brand + semantic
# colors so distinct categories stay visually distinguishable.
PALETTE = [PRIMARY, SECONDARY, WARNING, BRAND_DARK, DANGER, LIGHT, SUCCESS, "#9FC8E8"]

FONT_FAMILY = "Inter, Segoe UI, system-ui, sans-serif"

BASE_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(family=FONT_FAMILY, color=BRAND_DARK, size=12),
    margin=dict(l=40, r=20, t=30, b=40),
    height=320,
)

# Minimal mode bar -- keeps the PNG download (camera) button, drops the rest.
CHART_DOWNLOAD_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
        "autoScale2d", "resetScale2d", "hoverClosestCartesian",
        "hoverCompareCartesian", "toggleSpikelines",
    ],
}


def apply_theme(fig: go.Figure, **overrides) -> go.Figure:
    layout = {**BASE_LAYOUT, **overrides}
    fig.update_layout(**layout)
    return fig


def color_for(index: int) -> str:
    return PALETTE[index % len(PALETTE)]
