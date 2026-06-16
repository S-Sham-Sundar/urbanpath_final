"""
A* Algorithm — Heuristic-Guided Shortest Path
Developer A: Sham

A* improves on Dijkstra by using a heuristic h(n) to guide the search
toward the destination, pruning large parts of the graph.

f(n) = g(n) + h(n)
  g(n) = actual cost from src to n (same as Dijkstra's dist[n])
  h(n) = estimated cost from n to dst (Haversine distance — admissible)

Admissibility: h(n) never overestimates the true cost.
  Haversine gives straight-line distance in km — always ≤ road distance.
  This guarantees A* finds the optimal path.

Performance: 3–10× faster than Dijkstra on large city graphs because
the heuristic prunes nodes that are clearly "in the wrong direction."

Complexity: O(E log V) worst case, but typically much less in practice.
"""

from core.graph import Graph
from core.min_heap import MinHeap


def astar(graph: Graph, src: int, dst: int) -> tuple[float, list[int]]:
    """
    A* shortest path from src to dst using Haversine as the heuristic.

    Returns
    -------
    (distance, path)
      distance : float     — true shortest distance
      path     : list[int] — node IDs from src to dst
    """
    INF = float("inf")
    g_cost: dict[int, float] = {n: INF for n in graph.nodes}
    prev: dict[int, int | None] = {n: None for n in graph.nodes}
    g_cost[src] = 0.0

    # f = g + h; heap stores (f, node)
    heap = MinHeap()
    heap.push(graph.haversine(src, dst), src)

    closed: set[int] = set()

    while heap:
        f, u = heap.pop()

        if u in closed:
            continue
        closed.add(u)

        if u == dst:
            break

        for edge in graph.neighbors(u):
            v = edge.dst
            if v in closed:
                continue
            tentative_g = g_cost[u] + edge.weight
            if tentative_g < g_cost[v]:
                g_cost[v] = tentative_g
                prev[v] = u
                h = graph.haversine(v, dst)
                heap.push(tentative_g + h, v)

    return g_cost[dst], _reconstruct(prev, src, dst)


def _reconstruct(prev: dict, src: int, dst: int) -> list[int]:
    if prev[dst] is None and dst != src:
        return []
    path, cur = [], dst
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from core.graph import Graph
    from core.dijkstra import dijkstra

    g = Graph()
    for nid, lat, lon, name in [
        (0, 13.0827, 80.2707, "Central"),
        (1, 13.0500, 80.2824, "Marina"),
        (2, 13.0368, 80.2676, "Mylapore"),
        (3, 13.0012, 80.2565, "Adyar"),
    ]:
        g.add_node(nid, lat, lon, name)

    g.add_edge(0, 1, 4.2)
    g.add_edge(1, 2, 2.1)
    g.add_edge(2, 3, 3.8)
    g.add_edge(0, 2, 5.5)
    g.add_edge(0, 3, 12.0)

    a_dist, a_path = astar(g, 0, 3)
    d_dist, d_path = dijkstra(g, 0, 3)
    print(f"A*      : {a_path}, distance={a_dist:.2f}")
    print(f"Dijkstra: {d_path}, distance={d_dist:.2f}")
    print("Same result:", a_dist == d_dist)
