import networkx as nx


def build_graph(edges: list[tuple[str, str, int]], directed: bool = False) -> nx.Graph:
    """edges: [(source, target, weight), ...]"""
    graph = nx.DiGraph() if directed else nx.Graph()
    for source, target, weight in edges:
        if graph.has_edge(source, target):
            graph[source][target]["weight"] += weight
        else:
            graph.add_edge(source, target, weight=weight)
    return graph


def centrality_table(graph: nx.Graph) -> list[dict]:
    if graph.number_of_nodes() == 0:
        return []

    degree = dict(graph.degree())
    betweenness = nx.betweenness_centrality(graph)
    closeness = nx.closeness_centrality(graph)
    try:
        eigenvector = nx.eigenvector_centrality(graph, max_iter=1000)
    except (nx.PowerIterationFailedConvergence, nx.AmbiguousSolution, nx.NetworkXError):
        eigenvector = {n: 0.0 for n in graph.nodes()}
    pagerank = nx.pagerank(graph)

    rows = []
    for node in graph.nodes():
        rows.append(
            {
                "node": node,
                "degree": degree.get(node, 0),
                "betweenness": round(betweenness.get(node, 0.0), 4),
                "closeness": round(closeness.get(node, 0.0), 4),
                "eigenvector": round(eigenvector.get(node, 0.0), 4),
                "pagerank": round(pagerank.get(node, 0.0), 4),
            }
        )
    rows.sort(key=lambda r: r["degree"], reverse=True)
    return rows


def network_metrics(graph: nx.Graph) -> dict:
    if graph.number_of_nodes() == 0:
        return {"nodes": 0, "edges": 0}

    undirected = graph.to_undirected() if graph.is_directed() else graph
    components = list(nx.connected_components(undirected))
    largest = undirected.subgraph(max(components, key=len)) if components else undirected

    metrics = {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": round(nx.density(graph), 4),
        "connected_components": len(components),
        "clustering_coefficient": round(nx.average_clustering(undirected), 4),
    }

    if nx.is_connected(largest) and largest.number_of_nodes() > 1:
        metrics["diameter"] = nx.diameter(largest)
        metrics["average_path_length"] = round(nx.average_shortest_path_length(largest), 4)
    else:
        metrics["diameter"] = None
        metrics["average_path_length"] = None

    try:
        metrics["assortativity"] = round(nx.degree_assortativity_coefficient(graph), 4)
    except (ValueError, ZeroDivisionError):
        metrics["assortativity"] = None

    return metrics


def detect_communities(graph: nx.Graph, method: str = "louvain") -> dict:
    """Returns {node: community_id}. Louvain is networkx-native (3.0+);
    Girvan-Newman/Label Propagation also available without extra deps."""
    if graph.number_of_nodes() == 0:
        return {}

    undirected = graph.to_undirected() if graph.is_directed() else graph

    if method == "label_propagation":
        communities = nx.algorithms.community.label_propagation_communities(undirected)
    elif method == "greedy_modularity":
        communities = nx.algorithms.community.greedy_modularity_communities(undirected)
    else:
        communities = nx.algorithms.community.louvain_communities(undirected, seed=42)

    assignment = {}
    for idx, community in enumerate(communities):
        for node in community:
            assignment[node] = idx
    return assignment


def graph_figure(graph: nx.Graph, communities: dict | None = None, colors: list[str] | None = None):
    """Plotly figure of a NetworkX graph using a spring layout -- no extra
    graph-viz dependency needed beyond networkx + plotly already in use."""
    import plotly.graph_objects as go

    if graph.number_of_nodes() == 0:
        return go.Figure()

    pos = nx.spring_layout(graph, seed=42, k=1 / max(1, graph.number_of_nodes() ** 0.5))
    colors = colors or ["#052659", "#5483B3", "#D97706", "#040924", "#B3261E", "#7DA0CA", "#3F8F66", "#9FC8E8"]

    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="#7DA0CA"), hoverinfo="none")

    node_x = [pos[n][0] for n in graph.nodes()]
    node_y = [pos[n][1] for n in graph.nodes()]
    degree = dict(graph.degree())
    node_size = [8 + 4 * degree.get(n, 0) for n in graph.nodes()]
    node_color = [colors[communities.get(n, 0) % len(colors)] for n in graph.nodes()] if communities else "#052659"

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
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=10, r=10, t=10, b=10),
        height=500,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig
