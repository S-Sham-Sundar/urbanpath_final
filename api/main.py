"""
UrbanPath — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.routing import router as routing_router
from api.routes.search import router as search_router
from api.routes.isochrone import router as delivery_router

app = FastAPI(
    title="UrbanPath API",
    description="City-scale graph routing engine powered by custom DSA — no mapping libraries.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing_router, prefix="/api", tags=["Routing"])
app.include_router(search_router,  prefix="/api", tags=["Search"])
app.include_router(delivery_router, prefix="/api", tags=["Delivery"])


@app.get("/")
def root():
    return {
        "project": "UrbanPath",
        "description": "City-scale graph routing engine",
        "algorithms": [
            "Dijkstra", "A*", "BFS Isochrone",
            "Trie Autocomplete", "Held-Karp TSP",
            "K-means++", "Union-Find", "Kruskal MST", "Segment Tree",
        ],
        "endpoints": [
            "GET /api/route",
            "GET /api/isochrone",
            "GET /api/graph",
            "GET /api/search",
            "GET /api/connectivity",
            "GET /api/mst",
            "POST /api/delivery",
            "GET /api/traffic/{road_id}",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
