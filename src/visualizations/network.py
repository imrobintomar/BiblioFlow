import networkx as nx
import plotly.graph_objects as go

from visualizations.theme import BRAND_DARK, LIGHT, PALETTE, PRIMARY, apply_theme

# Cap on how many node labels render boldly -- biblioshiny's real network
# exports only bold-label the highest-degree nodes; everything else gets a
# faint small label (still legible on hover/zoom) instead of cluttering a
# dense graph with overlapping text.
MAX_BOLD_LABELS = 12


def network_chart(graph: nx.Graph, communities: dict | None = None, colors: list[str] | None = None) -> go.Figure:
    """Plotly figure of a NetworkX graph using a spring layout -- no extra
    graph-viz dependency needed beyond networkx + plotly already in use."""
    if graph.number_of_nodes() == 0:
        return go.Figure()

    pos = nx.spring_layout(graph, seed=42, k=1 / max(1, graph.number_of_nodes() ** 0.5))
    colors = colors or PALETTE
    degree = dict(graph.degree())

    edge_count = graph.number_of_edges()
    edge_opacity = max(0.06, min(0.5, 150 / max(1, edge_count)))
    edge_rgb = "125, 160, 202"  # LIGHT as rgb

    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color=f"rgba({edge_rgb}, {edge_opacity})"), hoverinfo="none",
    )

    nodes = list(graph.nodes())
    node_x = [pos[n][0] for n in nodes]
    node_y = [pos[n][1] for n in nodes]
    node_size = [8 + 4 * degree.get(n, 0) for n in nodes]
    node_color = [colors[communities.get(n, 0) % len(colors)] for n in nodes] if communities else PRIMARY

    # Faint small labels for every node (legible on hover/zoom, doesn't
    # dominate the figure visually).
    faint_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=nodes, textposition="top center",
        textfont=dict(size=7, color=LIGHT),
        hoverinfo="text",
        marker=dict(size=node_size, color=node_color, line=dict(width=1, color="#FFFFFF")),
    )

    # Bold dark labels for only the highest-degree nodes.
    top_nodes = sorted(nodes, key=lambda n: -degree.get(n, 0))[:MAX_BOLD_LABELS]
    bold_trace = go.Scatter(
        x=[pos[n][0] for n in top_nodes], y=[pos[n][1] for n in top_nodes],
        mode="text", text=top_nodes, textposition="top center",
        textfont=dict(size=12, color=BRAND_DARK), hoverinfo="skip",
    )

    fig = go.Figure(data=[edge_trace, faint_trace, bold_trace])
    return apply_theme(
        fig,
        showlegend=False,
        height=500,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
