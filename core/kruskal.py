"""
Kruskal's MST — Minimum Spanning Tree for Road Infrastructure
Developer B: Ajith

Finds the cheapest set of roads that keeps the entire city connected —
useful for infrastructure planning and visualising the backbone of the network.

Strategy:
  1. Sort all edges by weight  — O(E log E)
  2. Greedily add the cheapest edge that doesn't form a cycle (use DSU)
  3. Stop when we have V-1 edges  — the MST is complete

Total: O(E log E)
Without DSU the cycle-check would be O(V) per edge → O(E·V) total.
"""

from core.union_find import UnionFind


def kruskal_mst(num_nodes: int, edges: list[tuple]) -> tuple[list[tuple], float]:
    """
    Compute the Minimum Spanning Tree using Kruskal's algorithm.

    Parameters
    ----------
    num_nodes : int
        Total number of intersections (vertices) in the graph.
    edges : list of (weight, u, v)
        All road segments as (distance/cost, node_u, node_v).

    Returns
    -------
    mst_edges : list of (weight, u, v)
        The edges that form the MST.
    total_weight : float
        Sum of all edge weights in the MST.
    """
    # Step 1: sort edges by weight (cheapest first)
    sorted_edges = sorted(edges, key=lambda e: e[0])

    dsu = UnionFind(num_nodes)
    mst_edges: list[tuple] = []
    total_weight: float = 0.0

    # Step 2: greedily pick edges that don't form cycles
    for weight, u, v in sorted_edges:
        if dsu.union(u, v):            # returns True = different components
            mst_edges.append((weight, u, v))
            total_weight += weight
            if len(mst_edges) == num_nodes - 1:
                break                  # MST is complete — V-1 edges

    return mst_edges, total_weight


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Small city graph: 5 intersections, 7 roads
    #   (weight, node_u, node_v)
    sample_edges = [
        (2, 0, 1), (3, 0, 3), (6, 1, 2),
        (8, 1, 4), (5, 2, 4), (7, 3, 4), (9, 2, 3),
    ]
    mst, cost = kruskal_mst(5, sample_edges)
    print("MST edges:", mst)
    print("Total MST cost:", cost)   # should be 2+3+5+6 = 16
