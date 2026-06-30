import networkx as nx
import plotly.graph_objects as go

from visualizations.theme import LIGHT, PALETTE, PRIMARY, apply_theme


def network_chart(graph: nx.Graph, communities: dict | None = None, colors: list[str] | None = None) -> go.Figure:
    """Plotly figure of a NetworkX graph using a spring layout -- no extra
    graph-viz dependency needed beyond networkx + plotly already in use."""
    if graph.number_of_nodes() == 0:
        return go.Figure()

    pos = nx.spring_layout(graph, seed=42, k=1 / max(1, graph.number_of_nodes() ** 0.5))
    colors = colors or PALETTE

    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color=LIGHT), hoverinfo="none")

    node_x = [pos[n][0] for n in graph.nodes()]
    node_y = [pos[n][1] for n in graph.nodes()]
    degree = dict(graph.degree())
    node_size = [8 + 4 * degree.get(n, 0) for n in graph.nodes()]
    node_color = [colors[communities.get(n, 0) % len(colors)] for n in graph.nodes()] if communities else PRIMARY

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=list(graph.nodes()),
        textposition="top center",
        textfont=dict(size=9),
        hoverinfo="text",
        marker=dict(size=node_size, color=node_color, line=dict(width=1, color="#FFFFFF")),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    return apply_theme(
        fig,
        showlegend=False,
        height=500,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
