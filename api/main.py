"""
UrbanPath — FastAPI Application Entry Point
Loads the graph once at startup (OSM or synthetic fallback).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Graph is loaded once here and imported by route modules
from data.graph_generator import get_graph
GRAPH = get_graph()

from api.routes.routing import router as routing_router
from api.routes.search import router as search_router
from api.routes.isochrone import router as delivery_router

app = FastAPI(
    title="UrbanPath API",
    description=(
        "City-scale graph routing engine over OpenStreetMap — "
        "custom DSA, no mapping libraries."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing_router,  prefix="/api", tags=["Routing"])
app.include_router(search_router,   prefix="/api", tags=["Search"])
app.include_router(delivery_router, prefix="/api", tags=["Delivery"])


@app.get("/")
def root():
    return {
        "project": "UrbanPath",
        "version": "2.0.0",
        "data_source": "OpenStreetMap — Chennai road network",
        "graph": {
            "nodes": GRAPH.node_count(),
            "edges": GRAPH.edge_count(),
        },
        "algorithms": [
            "Dijkstra", "A* (Haversine)", "BFS Isochrone",
            "Trie Autocomplete", "Held-Karp TSP",
            "K-means++", "Union-Find", "Kruskal MST", "Segment Tree",
        ],
        "endpoints": [
            "GET  /api/route",
            "GET  /api/isochrone",
            "GET  /api/graph",
            "GET  /api/visualize",
            "GET  /api/search",
            "GET  /api/connectivity",
            "GET  /api/mst",
            "POST /api/delivery",
            "GET  /api/traffic/{road_id}",
        ],
        "cache": "Redis (5-min TTL) with in-memory fallback",
    }


@app.get("/health")
def health():
    from core import cache
    return {
        "status": "ok",
        "graph_nodes": GRAPH.node_count(),
        "redis": cache.REDIS_AVAILABLE,
    }
