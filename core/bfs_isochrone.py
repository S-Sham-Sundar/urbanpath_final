"""
BFS Isochrone — Reachability Maps
Developer A: Sham

Finds all nodes reachable from a source within a given time budget.
Complexity: O(V + E)
"""

from collections import deque
from core.graph import Graph


def bfs_isochrone(graph: Graph, src: int, time_limit: float) -> dict[int, float]:
    """
    Find all nodes reachable from src (integer index) within time_limit minutes.

    Returns dict mapping node_index → cumulative travel time.
    """
    reachable: dict[int, float] = {src: 0.0}
    queue = deque([(src, 0.0)])

    while queue:
        node, time_so_far = queue.popleft()
        for neighbor, weight in graph.neighbors_by_index(node):
            new_time = time_so_far + weight
            if new_time > time_limit:
                continue
            if neighbor not in reachable or new_time < reachable[neighbor]:
                reachable[neighbor] = new_time
                queue.append((neighbor, new_time))

    return reachable


def isochrone_boundary(
    graph: Graph, reachable: dict[int, float]
) -> list[tuple[float, float]]:
    """
    Return (lat, lon) of boundary nodes — reachable nodes with at least one
    neighbor outside the reachable set.
    """
    boundary = []
    reachable_set = set(reachable.keys())

    for idx in reachable_set:
        neighbors = {v for v, _ in graph.neighbors_by_index(idx)}
        if not neighbors.issubset(reachable_set):
            node = graph.get_node_by_index(idx)
            if node:
                boundary.append((node.lat, node.lon))

    return boundary
