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
