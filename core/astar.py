"""
A* Algorithm — Heuristic-Guided Shortest Path
Developer A: Sham

f(n) = g(n) + h(n)
  g(n) = actual cost from src to n
  h(n) = Haversine straight-line distance to dst (admissible heuristic)

Complexity: O(E log V) worst case, typically 3–10× faster than Dijkstra.
"""

from core.graph import Graph, haversine
from core.min_heap import MinHeap


def astar(graph: Graph, src: int, dst: int) -> tuple[float, list[int]]:
    """
    A* shortest path from src to dst (integer indices).
    Uses Haversine as admissible heuristic.

    Returns (distance_km, path_as_index_list). Returns (inf, []) if unreachable.
    """
    n = graph.node_count()
    INF = float("inf")
    g_cost = [INF] * n
    prev = [-1] * n
    g_cost[src] = 0.0

    dst_node = graph.get_node_by_index(dst)
    if dst_node is None:
        return INF, []

    def h(idx: int) -> float:
        node = graph.get_node_by_index(idx)
        if node is None:
            return 0.0
        return haversine(node.lat, node.lon, dst_node.lat, dst_node.lon)

    heap = MinHeap()
    heap.push(h(src), src)
    closed = set()

    while heap:
        f, u = heap.pop()
        if u in closed:
            continue
        closed.add(u)
        if u == dst:
            break
        for v, w in graph.neighbors_by_index(u):
            if v in closed:
                continue
            tg = g_cost[u] + w
            if tg < g_cost[v]:
                g_cost[v] = tg
                prev[v] = u
                heap.push(tg + h(v), v)

    if g_cost[dst] == INF:
        return INF, []
    return g_cost[dst], _reconstruct(prev, src, dst)


def _reconstruct(prev: list, src: int, dst: int) -> list[int]:
    if prev[dst] == -1 and dst != src:
        return []
    path, cur = [], dst
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path
