"""
BFS Isochrone — Reachability Maps
Developer A: Sham

An isochrone is the set of all locations reachable from a point within
a given time budget (e.g. "everywhere within 15 minutes").

Used by Uber for surge pricing zones, Zillow for commute-time filters,
and Google Maps for "things nearby" overlays.

Algorithm: BFS on a time-weighted graph.
  - Edge weights represent travel time in minutes.
  - BFS explores neighbors in order of cumulative travel time.
  - Any node whose cumulative time ≤ time_limit is "reachable."

Why BFS and not Dijkstra?
  For unweighted graphs, BFS is optimal (O(V + E) vs O(E log V)).
  Here we use a modified BFS with a deque and time tracking — effectively
  Dijkstra without the log-factor overhead for sparse, unit-ish weights.
  For true weighted isochrones, Dijkstra's dijkstra_all() is used.

Complexity: O(V + E)
"""

from collections import deque
from core.graph import Graph


def bfs_isochrone(graph: Graph, src: int, time_limit: float) -> dict[int, float]:
    """
    Find all nodes reachable from src within time_limit minutes.

    Parameters
    ----------
    graph      : Graph — road network with edge weights as travel time (minutes)
    src        : int   — starting node ID
    time_limit : float — maximum travel time in minutes

    Returns
    -------
    reachable : dict[int, float]
        Maps node_id → travel time from src. Only includes nodes within limit.
    """
    reachable: dict[int, float] = {src: 0.0}
    queue = deque([(src, 0.0)])     # (node, cumulative_time)

    while queue:
        node, time_so_far = queue.popleft()

        for edge in graph.neighbors(node):
            neighbor = edge.dst
            new_time = time_so_far + edge.weight

            if new_time > time_limit:
                continue                        # outside the isochrone

            if neighbor not in reachable or new_time < reachable[neighbor]:
                reachable[neighbor] = new_time
                queue.append((neighbor, new_time))

    return reachable


def isochrone_boundary(
    graph: Graph, reachable: dict[int, float]
) -> list[tuple[float, float]]:
    """
    Extract the boundary nodes of the isochrone — nodes that have at least
    one neighbor NOT in the reachable set. These form the outer edge of the
    reachability polygon drawn on the map.

    Returns list of (lat, lon) for boundary nodes.
    """
    boundary = []
    reachable_set = set(reachable.keys())

    for node_id in reachable_set:
        neighbors = {e.dst for e in graph.neighbors(node_id)}
        if not neighbors.issubset(reachable_set):
            n = graph.nodes[node_id]
            boundary.append((n.lat, n.lon))

    return boundary


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from core.graph import Graph

    g = Graph()
    # Nodes with travel-time edges (minutes)
    for nid, lat, lon, name in [
        (0, 13.0827, 80.2707, "Central"),
        (1, 13.0500, 80.2824, "Marina"),
        (2, 13.0368, 80.2676, "Mylapore"),
        (3, 13.0012, 80.2565, "Adyar"),
        (4, 13.0850, 80.2101, "Anna Nagar"),
        (5, 13.1200, 80.2300, "Ambattur"),
    ]:
        g.add_node(nid, lat, lon, name)

    g.add_edge(0, 1, 8.0)    # 8 minutes
    g.add_edge(0, 4, 12.0)
    g.add_edge(1, 2, 5.0)
    g.add_edge(2, 3, 9.0)
    g.add_edge(4, 5, 15.0)

    reachable = bfs_isochrone(g, src=0, time_limit=15.0)
    print("Reachable within 15 min from Central:")
    for nid, t in sorted(reachable.items(), key=lambda x: x[1]):
        print(f"  {g.nodes[nid].name}: {t:.1f} min")

    boundary = isochrone_boundary(g, reachable)
    print(f"Boundary nodes: {len(boundary)}")
