"""
Routing API — /route and /isochrone endpoints
Developer A: Sham
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from data.graph_generator import generate_city_graph, load_graph_from_dict
from core.dijkstra import dijkstra
from core.astar import astar
from core.bfs_isochrone import bfs_isochrone, isochrone_boundary

router = APIRouter()

# Load graph once at module level (in production, load from DB/Redis)
_graph_data = generate_city_graph(rows=15, cols=15)
GRAPH = load_graph_from_dict(_graph_data)


class RouteResponse(BaseModel):
    algorithm: str
    src: int
    dst: int
    distance: float
    path: list[int]
    path_coords: list[dict]


class IsochroneResponse(BaseModel):
    src: int
    time_limit: float
    reachable_count: int
    reachable: list[dict]
    boundary: list[dict]


@router.get("/route", response_model=RouteResponse)
def get_route(
    src: int = Query(..., description="Source node ID"),
    dst: int = Query(..., description="Destination node ID"),
    algorithm: str = Query("astar", description="'dijkstra' or 'astar'"),
):
    """
    Find the shortest path between two nodes.
    Returns the path as a sequence of node IDs and their coordinates.
    """
    if src not in GRAPH.nodes:
        raise HTTPException(404, f"Source node {src} not found")
    if dst not in GRAPH.nodes:
        raise HTTPException(404, f"Destination node {dst} not found")

    if algorithm == "dijkstra":
        distance, path = dijkstra(GRAPH, src, dst)
    else:
        distance, path = astar(GRAPH, src, dst)

    if not path:
        raise HTTPException(404, "No path found between these nodes")

    path_coords = [
        {"id": nid, "lat": GRAPH.nodes[nid].lat, "lon": GRAPH.nodes[nid].lon}
        for nid in path
    ]

    return RouteResponse(
        algorithm=algorithm,
        src=src,
        dst=dst,
        distance=round(distance, 4),
        path=path,
        path_coords=path_coords,
    )


@router.get("/isochrone", response_model=IsochroneResponse)
def get_isochrone(
    src: int = Query(..., description="Source node ID"),
    time_limit: float = Query(15.0, description="Time limit in minutes"),
):
    """
    Compute the isochrone — all nodes reachable from src within time_limit.
    """
    if src not in GRAPH.nodes:
        raise HTTPException(404, f"Node {src} not found")

    reachable = bfs_isochrone(GRAPH, src, time_limit)
    boundary_coords = isochrone_boundary(GRAPH, reachable)

    reachable_list = [
        {
            "id": nid,
            "lat": GRAPH.nodes[nid].lat,
            "lon": GRAPH.nodes[nid].lon,
            "time": round(t, 2),
        }
        for nid, t in sorted(reachable.items(), key=lambda x: x[1])
    ]

    return IsochroneResponse(
        src=src,
        time_limit=time_limit,
        reachable_count=len(reachable),
        reachable=reachable_list,
        boundary=[{"lat": lat, "lon": lon} for lat, lon in boundary_coords],
    )


@router.get("/graph")
def get_graph_info():
    """Return basic graph stats and a sample of nodes for the frontend."""
    sample_nodes = [
        {"id": n.id, "lat": n.lat, "lon": n.lon, "name": n.name}
        for n in list(GRAPH.nodes.values())[:50]
    ]
    return {
        "num_nodes": GRAPH.num_nodes,
        "num_edges": GRAPH.num_edges,
        "sample_nodes": sample_nodes,
    }
