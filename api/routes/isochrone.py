"""
Delivery API — /delivery, /traffic
Developer B: Ajith

Held-Karp TSP with naive-baseline comparison + Redis caching + latency.
"""

import time
import math
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.tsp_held_karp import held_karp, euclidean_dist_matrix
from core.kmeans import kmeans_cluster, recommend_k
from core.segment_tree import SegmentTree
from core import cache
import random

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _naive_nearest_neighbour(dist: list[list[float]]) -> float:
    """
    Greedy nearest-neighbour TSP baseline — O(n²).
    Visits the closest unvisited node at every step.
    Used to compute the % improvement Held-Karp achieves.
    """
    n = len(dist)
    visited = [False] * n
    visited[0] = True
    current = 0
    total = 0.0
    for _ in range(n - 1):
        best_dist = math.inf
        best_next = -1
        for j in range(n):
            if not visited[j] and dist[current][j] < best_dist:
                best_dist = dist[current][j]
                best_next = j
        visited[best_next] = True
        total += best_dist
        current = best_next
    total += dist[current][0]   # return to depot
    return total


# ── Models ────────────────────────────────────────────────────────────────────

class Stop(BaseModel):
    id: int
    lat: float
    lon: float
    name: str = ""


class DeliveryRequest(BaseModel):
    stops: list[Stop] = Field(..., min_length=2, max_length=100)


class DeliveryResponse(BaseModel):
    total_stops: int
    strategy: str
    clusters: list[list[int]]
    optimal_route: list[int]
    estimated_distance: float
    naive_distance: float
    reduction_pct: float           # % improvement over greedy baseline
    latency_ms: float = 0.0


class TrafficResponse(BaseModel):
    road_id: str
    hour_range: list[int]
    min_traffic: float
    total_traffic: float
    best_hour: int
    latency_ms: float = 0.0


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/delivery", response_model=DeliveryResponse)
def optimise_delivery(request: DeliveryRequest):
    """
    Multi-stop delivery optimisation.

    ≤ 20 stops : Held-Karp exact TSP
    > 20 stops : K-means++ cluster-first, then Held-Karp per cluster

    Returns the route, estimated distance, naive baseline distance,
    and the % reduction Held-Karp achieves over greedy nearest-neighbour.
    """
    stops = request.stops
    n = len(stops)
    points = [(s.lat, s.lon) for s in stops]

    t0 = time.perf_counter()

    if n <= 20:
        dist_matrix = euclidean_dist_matrix(points)

        # Baseline
        naive_dist = _naive_nearest_neighbour(dist_matrix)

        # Held-Karp exact
        cost, route = held_karp(dist_matrix)

        reduction = round((naive_dist - cost) / naive_dist * 100, 2) if naive_dist > 0 else 0.0

        latency_ms = round((time.perf_counter() - t0) * 1000, 3)

        return DeliveryResponse(
            total_stops=n,
            strategy="exact",
            clusters=[list(range(n))],
            optimal_route=route,
            estimated_distance=round(cost, 6),
            naive_distance=round(naive_dist, 6),
            reduction_pct=reduction,
            latency_ms=latency_ms,
        )
    else:
        k = recommend_k(n, max_cluster_size=15)
        clusters = kmeans_cluster(points, k)

        full_route = []
        total_cost = 0.0
        total_naive = 0.0

        for cluster in clusters:
            cluster_points = [points[i] for i in cluster]
            dm = euclidean_dist_matrix(cluster_points)
            cost, local_route = held_karp(dm)
            total_cost += cost
            total_naive += _naive_nearest_neighbour(dm)
            full_route.extend([cluster[i] for i in local_route[:-1]])

        full_route.append(full_route[0])
        reduction = round((total_naive - total_cost) / total_naive * 100, 2) if total_naive > 0 else 0.0
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)

        return DeliveryResponse(
            total_stops=n,
            strategy="clustered",
            clusters=clusters,
            optimal_route=full_route,
            estimated_distance=round(total_cost, 6),
            naive_distance=round(total_naive, 6),
            reduction_pct=reduction,
            latency_ms=latency_ms,
        )


@router.get("/traffic/{road_id}", response_model=TrafficResponse)
def get_traffic(road_id: str, start_hour: int = 0, end_hour: int = 23):
    """
    Segment Tree range-min query over 168-bucket (7-day × 24hr) traffic data.
    O(log n) per query.
    """
    if start_hour < 0 or end_hour > 23 or start_hour > end_hour:
        raise HTTPException(400, "Invalid hour range (0–23)")

    cache_key = cache.make_key("traffic", road_id, start_hour, end_hour)
    cached = cache.get(cache_key)
    if cached:
        return cached

    t0 = time.perf_counter()

    rng = random.Random(hash(road_id) % (2 ** 32))
    # 7 days × 24 hours = 168 buckets
    weekly = [round(rng.uniform(0.2, 2.0), 2) for _ in range(168)]
    for day in range(7):
        for h in [8, 9, 17, 18, 19]:
            idx = day * 24 + h
            weekly[idx] = round(min(weekly[idx] * 2.2, 2.0), 2)

    # Query today's hours (day 0)
    today = weekly[:24]
    st = SegmentTree(today)

    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    result = TrafficResponse(
        road_id=road_id,
        hour_range=[start_hour, end_hour],
        min_traffic=round(st.range_min(start_hour, end_hour), 2),
        total_traffic=round(st.range_sum(start_hour, end_hour), 2),
        best_hour=st.best_travel_hour(start_hour, end_hour),
        latency_ms=latency_ms,
    ).model_dump()
    cache.set(cache_key, result, ttl=300)
    return result
