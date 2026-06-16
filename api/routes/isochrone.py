"""
Delivery API — /delivery endpoint
Developer B: Ajith

Exposes Held-Karp TSP and K-means++ clustering over HTTP.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.tsp_held_karp import held_karp, euclidean_dist_matrix
from core.kmeans import kmeans_cluster, recommend_k
from core.segment_tree import SegmentTree
import random

router = APIRouter()


class Stop(BaseModel):
    id: int
    lat: float
    lon: float
    name: str = ""


class DeliveryRequest(BaseModel):
    stops: list[Stop] = Field(..., min_length=2, max_length=100)


class DeliveryResponse(BaseModel):
    total_stops: int
    strategy: str                   # "exact" or "clustered"
    clusters: list[list[int]]       # cluster assignments (by stop index)
    optimal_route: list[int]        # ordered stop indices
    estimated_distance: float


class TrafficResponse(BaseModel):
    road_id: str
    hour_range: list[int]
    min_traffic: float
    total_traffic: float
    best_hour: int


@router.post("/delivery", response_model=DeliveryResponse)
def optimise_delivery(request: DeliveryRequest):
    """
    Optimise a multi-stop delivery route.

    ≤ 20 stops : Held-Karp exact TSP — guaranteed optimal
    > 20 stops : K-means++ cluster-first, then Held-Karp per cluster
    """
    stops = request.stops
    n = len(stops)
    points = [(s.lat, s.lon) for s in stops]

    if n <= 20:
        # Exact solution
        dist_matrix = euclidean_dist_matrix(points)
        cost, route = held_karp(dist_matrix)
        return DeliveryResponse(
            total_stops=n,
            strategy="exact",
            clusters=[list(range(n))],
            optimal_route=route,
            estimated_distance=round(cost, 6),
        )
    else:
        # Cluster-first for large inputs
        k = recommend_k(n, max_cluster_size=15)
        clusters = kmeans_cluster(points, k)

        # Run Held-Karp on each cluster; stitch routes together
        full_route = []
        total_cost = 0.0
        for cluster in clusters:
            cluster_points = [points[i] for i in cluster]
            dist_matrix = euclidean_dist_matrix(cluster_points)
            cost, local_route = held_karp(dist_matrix)
            full_route.extend([cluster[i] for i in local_route[:-1]])
            total_cost += cost

        full_route.append(full_route[0])   # return to depot

        return DeliveryResponse(
            total_stops=n,
            strategy="clustered",
            clusters=clusters,
            optimal_route=full_route,
            estimated_distance=round(total_cost, 6),
        )


@router.get("/traffic/{road_id}", response_model=TrafficResponse)
def get_traffic(
    road_id: str,
    start_hour: int = 0,
    end_hour: int = 23,
):
    """
    Query traffic data for a road using the Segment Tree.
    Returns min traffic, total traffic, and best travel hour in the window.
    In production, load real readings from PostgreSQL.
    """
    if start_hour < 0 or end_hour > 23 or start_hour > end_hour:
        raise HTTPException(400, "Invalid hour range (0–23)")

    # Simulate 24 hours of traffic readings for this road
    rng = random.Random(hash(road_id) % (2 ** 32))
    hourly = [round(rng.uniform(0.2, 2.0), 2) for _ in range(24)]
    # Add realistic rush-hour spikes
    for h in [8, 9, 17, 18, 19]:
        hourly[h] = round(min(hourly[h] * 2.2, 2.0), 2)

    st = SegmentTree(hourly)

    return TrafficResponse(
        road_id=road_id,
        hour_range=[start_hour, end_hour],
        min_traffic=round(st.range_min(start_hour, end_hour), 2),
        total_traffic=round(st.range_sum(start_hour, end_hour), 2),
        best_hour=st.best_travel_hour(start_hour, end_hour),
    )
