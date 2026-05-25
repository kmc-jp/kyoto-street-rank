import networkx as nx


# NetworkX calls the PageRank damping factor "alpha".
PAGERANK_ALPHA = 0.85
RANKING_METHODS = {
    "pagerank": "PageRank",
    "win_loss": "勝敗差",
}


def calculate_ranking(intersections, method="pagerank"):
    rows = build_ranking_rows(intersections)
    if method == "win_loss":
        return sorted(
            rows,
            key=lambda row: (row["win_loss"], row["wins"], -row["losses"], row["pagerank"], row["name"]),
            reverse=True,
        )
    return sorted(rows, key=lambda row: (row["pagerank"], row["win_loss"], row["wins"], row["name"]), reverse=True)


def build_ranking_rows(intersections):
    graph = nx.DiGraph()
    wins = {}
    losses = {}

    for intersection in intersections:
        winner = intersection.winner.name
        loser = intersection.loser.name
        graph.add_edge(loser, winner)
        wins[winner] = wins.get(winner, 0) + 1
        wins.setdefault(loser, 0)
        losses[loser] = losses.get(loser, 0) + 1
        losses.setdefault(winner, 0)

    if not graph:
        return []

    pageranks = nx.pagerank(graph, alpha=PAGERANK_ALPHA)
    return [
        {
            "name": name,
            "pagerank": pagerank,
            "wins": wins.get(name, 0),
            "losses": losses.get(name, 0),
            "win_loss": wins.get(name, 0) - losses.get(name, 0),
        }
        for name, pagerank in pageranks.items()
    ]
