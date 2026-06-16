"""
Routing API — /route, /isochrone, /graph, /visualize
Developer A: Sham

Redis-cached shortest paths + latency headers + D3 traversal steps.
"""

import time
import sys
import os

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.dijkstra import dijkstra
from core.astar import astar
from core.bfs_isochrone import bfs_isochrone, isochrone_boundary
from core import cache

router = APIRouter()


# ── Models ────────────────────────────────────────────────────────────────────

class RouteResponse(BaseModel):
    algorithm: str
    src: int
    dst: int
    distance: float
    path: list[int]
    path_coords: list[dict]
    latency_ms: float = 0.0
    cache_hit: bool = False


class IsochroneResponse(BaseModel):
    src: int
    time_limit: float
    reachable_count: int
    reachable: list[dict]
    boundary: list[dict]
    latency_ms: float = 0.0


class VisualizeResponse(BaseModel):
    algorithm: str
    src: int
    dst: int
    steps: list[dict]   # each step: {step, current, visited, frontier, path}
    final_path: list[int]
    total_steps: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/route", response_model=RouteResponse)
def get_route(
    src: int = Query(..., description="Source node index"),
    dst: int = Query(..., description="Destination node index"),
    algorithm: str = Query("astar", description="'dijkstra' or 'astar'"),
):
    """
    Shortest path via Dijkstra or A* (Haversine heuristic).
    Results cached in Redis for 5 minutes.
    """
    from api.main import GRAPH

    n = GRAPH.node_count()
    if not (0 <= src < n):
        raise HTTPException(404, f"Source node {src} out of range (0–{n-1})")
    if not (0 <= dst < n):
        raise HTTPException(404, f"Destination node {dst} out of range (0–{n-1})")

    cache_key = cache.make_key("route", algorithm, src, dst)
    cached = cache.get(cache_key)
    if cached:
        cached["cache_hit"] = True
        return cached

    t0 = time.perf_counter()

    if algorithm == "dijkstra":
        distance, path = dijkstra(GRAPH, src, dst)
    else:
        distance, path = astar(GRAPH, src, dst)

    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    if not path:
        raise HTTPException(404, "No path found between these nodes")

    path_coords = []
    for idx in path:
        node = GRAPH.get_node_by_index(idx)
        if node:
            path_coords.append({"id": idx, "lat": node.lat, "lon": node.lon,
                                 "name": node.name})

    result = RouteResponse(
        algorithm=algorithm,
        src=src,
        dst=dst,
        distance=round(distance, 4),
        path=path,
        path_coords=path_coords,
        latency_ms=latency_ms,
        cache_hit=False,
    ).model_dump()

    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/isochrone", response_model=IsochroneResponse)
def get_isochrone(
    src: int = Query(..., description="Source node index"),
    time_limit: float = Query(15.0, description="Time limit in minutes"),
):
    """
    BFS isochrone — all nodes reachable within time_limit minutes.
    """
    from api.main import GRAPH

    n = GRAPH.node_count()
    if not (0 <= src < n):
        raise HTTPException(404, f"Node {src} out of range (0–{n-1})")

    t0 = time.perf_counter()
    reachable = bfs_isochrone(GRAPH, src, time_limit)
    boundary_coords = isochrone_boundary(GRAPH, reachable)
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    src_node = GRAPH.get_node_by_index(src)
    reachable_list = []
    for idx, t in sorted(reachable.items(), key=lambda x: x[1]):
        node = GRAPH.get_node_by_index(idx)
        if node:
            reachable_list.append({
                "id": idx, "lat": node.lat, "lon": node.lon, "time": round(t, 2)
            })

    return IsochroneResponse(
        src=src,
        time_limit=time_limit,
        reachable_count=len(reachable),
        reachable=reachable_list,
        boundary=[{"lat": lat, "lon": lon} for lat, lon in boundary_coords],
        latency_ms=latency_ms,
    )


@router.get("/graph")
def get_graph_info():
    """Graph stats + sample nodes for the D3 visualiser frontend."""
    from api.main import GRAPH
    return GRAPH.to_dict(max_nodes=300)


@router.get("/visualize", response_model=VisualizeResponse)
def visualize_traversal(
    src: int = Query(..., description="Source node index"),
    dst: int = Query(..., description="Destination node index"),
    algorithm: str = Query("dijkstra", description="'dijkstra' or 'bfs'"),
    max_nodes: int = Query(200, description="Subgraph size for visualisation"),
):
    """
    Return step-by-step traversal of Dijkstra or BFS for D3 playback.
    Works on a local subgraph for performance.
    """
    from api.main import GRAPH

    n = min(GRAPH.node_count(), max_nodes)
    if not (0 <= src < n):
        src = 0
    if not (0 <= dst < n):
        dst = min(n - 1, 50)

    steps = []
    visited: list[int] = []
    frontier: list[int] = []

    if algorithm == "dijkstra":
        import heapq
        dist = [float("inf")] * n
        prev = [-1] * n
        dist[src] = 0
        heap = [(0.0, src)]
        step_n = 0

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            visited.append(u)
            frontier = [item[1] for item in heap]
            steps.append({
                "step": step_n,
                "current": u,
                "dist": round(d, 4),
                "visited": list(visited[-30:]),
                "frontier": frontier[:20],
            })
            step_n += 1
            if u == dst:
                break
            for nbr, w in GRAPH.neighbors_by_index(u):
                if nbr >= n:
                    continue
                nd = d + w
                if nd < dist[nbr]:
                    dist[nbr] = nd
                    prev[nbr] = u
                    heapq.heappush(heap, (nd, nbr))

        # Reconstruct path
        path = []
        cur = dst
        while cur != -1:
            path.append(cur)
            cur = prev[cur]
        path.reverse()

    else:  # BFS
        from collections import deque
        visited_set = set()
        prev = [-1] * n
        queue = deque([src])
        visited_set.add(src)
        step_n = 0
        path = []

        while queue:
            u = queue.popleft()
            visited.append(u)
            frontier = list(queue)[:20]
            steps.append({
                "step": step_n,
                "current": u,
                "dist": 0,
                "visited": list(visited[-30:]),
                "frontier": frontier,
            })
            step_n += 1
            if u == dst:
                break
            for nbr, _ in GRAPH.neighbors_by_index(u):
                if nbr >= n or nbr in visited_set:
                    continue
                visited_set.add(nbr)
                prev[nbr] = u
                queue.append(nbr)

        cur = dst
        while cur != -1:
            path.append(cur)
            cur = prev[cur]
        path.reverse()

    return VisualizeResponse(
        algorithm=algorithm,
        src=src,
        dst=dst,
        steps=steps[:500],   # cap at 500 steps for response size
        final_path=path,
        total_steps=len(steps),
    )
