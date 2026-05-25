import networkx as nx


def calculate_ranking(intersections):
    graph = nx.DiGraph()
    for intersection in intersections:
        graph.add_edge(intersection.loser.name, intersection.winner.name)

    if not graph:
        return []

    scores = nx.pagerank(graph)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
