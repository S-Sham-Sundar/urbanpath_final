"""
Dijkstra's Algorithm — Single-Source Shortest Path
Developer A: Sham

Complexity: O(E log V) with a binary heap.
"""

from core.graph import Graph
from core.min_heap import MinHeap


def dijkstra(graph: Graph, src: int, dst: int) -> tuple[float, list[int]]:
    """
    Shortest path from src to dst (integer indices) using Dijkstra's algorithm.

    Returns (distance_km, path_as_index_list). Returns (inf, []) if unreachable.
    """
    n = graph.node_count()
    INF = float("inf")
    dist = [INF] * n
    prev = [-1] * n
    dist[src] = 0.0

    heap = MinHeap()
    heap.push(0.0, src)
    visited = set()

    while heap:
        d, u = heap.pop()
        if u in visited:
            continue
        visited.add(u)
        if u == dst:
            break
        for v, w in graph.neighbors_by_index(u):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heap.push(nd, v)

    if dist[dst] == INF:
        return INF, []
    return dist[dst], _reconstruct(prev, src, dst)


def _reconstruct(prev: list, src: int, dst: int) -> list[int]:
    if prev[dst] == -1 and dst != src:
        return []
    path, cur = [], dst
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def dijkstra_all(graph: Graph, src: int) -> dict[int, tuple[float, list[int]]]:
    """Shortest paths from src to ALL reachable nodes."""
    n = graph.node_count()
    INF = float("inf")
    dist = [INF] * n
    prev = [-1] * n
    dist[src] = 0.0

    heap = MinHeap()
    heap.push(0.0, src)
    visited = set()

    while heap:
        d, u = heap.pop()
        if u in visited:
            continue
        visited.add(u)
        for v, w in graph.neighbors_by_index(u):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heap.push(nd, v)

    return {
        i: (dist[i], _reconstruct(prev, src, i))
        for i in range(n)
        if dist[i] < INF
    }
