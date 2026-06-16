"""
Held-Karp TSP — Exact Multi-Stop Delivery Optimisation
Developer B: Ajith

Given ≤ 20 delivery stops, find the shortest route that visits every stop
exactly once and returns to the depot.

Why not greedy nearest-neighbour?
  Greedy gives ~20–25% suboptimal routes. For a delivery business, that's
  wasted fuel on every single run. Held-Karp guarantees the exact optimum.

Algorithm: Bitmask Dynamic Programming
  State: dp[mask][i] = shortest distance to have visited exactly the stops
         in `mask`, ending at stop i.
  Transition: dp[mask | (1 << j)][j] = dp[mask][i] + dist[i][j]

Time:  O(2ⁿ · n²)  — feasible up to n ≈ 20
Space: O(2ⁿ · n)

For n > 20 stops, use K-means++ clustering (see kmeans.py) to split into
groups, then run Held-Karp on each cluster.
"""

import math


def held_karp(dist: list[list[float]]) -> tuple[float, list[int]]:
    """
    Solve the Travelling Salesman Problem exactly using bitmask DP.

    Parameters
    ----------
    dist : n×n distance matrix  (dist[i][j] = cost from stop i to stop j)

    Returns
    -------
    min_cost : float
        Total distance of the optimal route.
    path : list[int]
        Ordered list of stop indices, starting and ending at stop 0 (depot).
    """
    n = len(dist)
    if n == 0:
        return 0.0, []
    if n == 1:
        return 0.0, [0]

    INF = float("inf")
    FULL = (1 << n) - 1        # bitmask with all n stops visited

    # dp[mask][i] = min cost to reach stop i having visited exactly `mask`
    dp: list[list[float]] = [[INF] * n for _ in range(1 << n)]
    # parent[mask][i] = the previous stop on the optimal path to (mask, i)
    parent: list[list[int]] = [[-1] * n for _ in range(1 << n)]

    dp[1][0] = 0.0             # start at depot (stop 0), mask = 0b0001

    for mask in range(1 << n):
        for i in range(n):
            if dp[mask][i] == INF:
                continue
            if not (mask >> i & 1):
                continue       # stop i not in current mask — skip

            # try extending to each unvisited stop j
            for j in range(n):
                if mask >> j & 1:
                    continue   # j already visited
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + dist[i][j]
                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i

    # find the best last stop before returning to depot
    min_cost = INF
    last = -1
    for i in range(1, n):
        cost = dp[FULL][i] + dist[i][0]
        if cost < min_cost:
            min_cost = cost
            last = i

    # reconstruct the path by following parent pointers
    path = []
    mask = FULL
    curr = last
    while curr != -1:
        path.append(curr)
        prev = parent[mask][curr]
        mask ^= (1 << curr)
        curr = prev
    path.reverse()
    path.append(0)             # return to depot

    return min_cost, path


def euclidean_dist_matrix(points: list[tuple[float, float]]) -> list[list[float]]:
    """Build an n×n Euclidean distance matrix from (lat, lon) coordinates."""
    n = len(points)
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dy = points[i][0] - points[j][0]
                dx = points[i][1] - points[j][1]
                dist[i][j] = math.sqrt(dy * dy + dx * dx)
    return dist


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 5 delivery stops as (lat, lon)
    stops = [
        (13.0827, 80.2707),   # depot
        (13.0500, 80.2824),
        (13.0368, 80.2676),
        (13.0012, 80.2565),
        (13.0850, 80.2101),
    ]
    dist_matrix = euclidean_dist_matrix(stops)
    cost, route = held_karp(dist_matrix)
    print(f"Optimal route: {route}")
    print(f"Total distance: {cost:.4f}")
