"""
Dijkstra's Algorithm — Single-Source Shortest Path
Developer A: Sham

Finds the shortest path between two intersections in the road network.
Uses the custom MinHeap (no heapq) to maintain the priority frontier.

Why not BFS?
  BFS finds the shortest path by hop count, not by distance.
  Roads have variable weights — a 2-hop route via a highway can be
  shorter than a 1-hop route through a congested lane. We need a
  priority queue to always expand the cheapest known path first.

Complexity: O(E log V) with a binary heap.
"""

from core.graph import Graph
from core.min_heap import MinHeap


def dijkstra(graph: Graph, src: int, dst: int) -> tuple[float, list[int]]:
    """
    Shortest path from src to dst using Dijkstra's algorithm.

    Parameters
    ----------
    graph : Graph — the city road network
    src   : int   — source node ID
    dst   : int   — destination node ID

    Returns
    -------
    (distance, path)
      distance : float     — total shortest distance (inf if unreachable)
      path     : list[int] — ordered list of node IDs from src to dst
    """
    INF = float("inf")
    dist: dict[int, float] = {n: INF for n in graph.nodes}
    prev: dict[int, int | None] = {n: None for n in graph.nodes}
    dist[src] = 0.0

    heap = MinHeap()
    heap.push(0.0, src)

    visited: set[int] = set()

    while heap:
        d, u = heap.pop()

        if u in visited:
            continue                   # stale entry — skip
        visited.add(u)

        if u == dst:
            break                      # found the shortest path to dst

        for edge in graph.neighbors(u):
            v = edge.dst
            if v in visited:
                continue
            new_dist = d + edge.weight
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                heap.push(new_dist, v)

    return dist[dst], _reconstruct_path(prev, src, dst)


def _reconstruct_path(prev: dict, src: int, dst: int) -> list[int]:
    """Walk the prev-pointer chain from dst back to src, then reverse."""
    if prev[dst] is None and dst != src:
        return []                      # no path found
    path = []
    cur = dst
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def dijkstra_all(graph: Graph, src: int) -> dict[int, tuple[float, list[int]]]:
    """
    Shortest paths from src to ALL reachable nodes.
    Used for isochrone computation — returns {node: (distance, path)}.
    """
    INF = float("inf")
    dist: dict[int, float] = {n: INF for n in graph.nodes}
    prev: dict[int, int | None] = {n: None for n in graph.nodes}
    dist[src] = 0.0

    heap = MinHeap()
    heap.push(0.0, src)
    visited: set[int] = set()

    while heap:
        d, u = heap.pop()
        if u in visited:
            continue
        visited.add(u)
        for edge in graph.neighbors(u):
            v = edge.dst
            if v not in visited:
                new_dist = d + edge.weight
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heap.push(new_dist, v)

    return {
        n: (dist[n], _reconstruct_path(prev, src, n))
        for n in graph.nodes
        if dist[n] < INF
    }


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from core.graph import Graph
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

    dist, path = dijkstra(g, 0, 3)
    print(f"Shortest path 0→3: {path}, distance: {dist:.2f} km")
