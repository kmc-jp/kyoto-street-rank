import networkx as nx


# NetworkX calls the PageRank damping factor "alpha".
PAGERANK_ALPHA = 0.85


def calculate_ranking(intersections):
    graph = nx.DiGraph()
    for intersection in intersections:
        graph.add_edge(intersection.loser.name, intersection.winner.name)

    if not graph:
        return []

    scores = nx.pagerank(graph, alpha=PAGERANK_ALPHA)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
