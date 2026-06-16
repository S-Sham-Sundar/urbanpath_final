"""
Search API — /search endpoint
Developer B: Ajith

Exposes the Trie autocomplete and MST viewer over HTTP.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from core.trie import Trie
from core.kruskal import kruskal_mst
from core.union_find import UnionFind
from data.graph_generator import generate_city_graph, load_graph_from_dict

router = APIRouter()

# ── Bootstrap Trie with location data ────────────────────────────────────────
_LOCATIONS = [
    ("Marina Beach",       {"lat": 13.0500, "lon": 80.2824, "type": "beach"}),
    ("Mall of Chennai",    {"lat": 13.0200, "lon": 80.2500, "type": "mall"}),
    ("Mandaveli",          {"lat": 13.0209, "lon": 80.2674, "type": "area"}),
    ("Mount Road",         {"lat": 13.0604, "lon": 80.2496, "type": "road"}),
    ("Mylapore",           {"lat": 13.0368, "lon": 80.2676, "type": "area"}),
    ("Anna Nagar",         {"lat": 13.0850, "lon": 80.2101, "type": "area"}),
    ("Adyar",              {"lat": 13.0012, "lon": 80.2565, "type": "area"}),
    ("T Nagar",            {"lat": 13.0418, "lon": 80.2341, "type": "area"}),
    ("Tambaram",           {"lat": 12.9249, "lon": 80.1000, "type": "suburb"}),
    ("Velachery",          {"lat": 12.9815, "lon": 80.2180, "type": "area"}),
    ("Guindy",             {"lat": 13.0067, "lon": 80.2206, "type": "area"}),
    ("Koyambedu",          {"lat": 13.0694, "lon": 80.1948, "type": "area"}),
    ("Central Station",    {"lat": 13.0827, "lon": 80.2707, "type": "transit"}),
    ("Chennai Airport",    {"lat": 12.9941, "lon": 80.1709, "type": "transit"}),
    ("Santhome",           {"lat": 13.0330, "lon": 80.2771, "type": "area"}),
    ("Besant Nagar",       {"lat": 13.0002, "lon": 80.2683, "type": "area"}),
    ("Porur",              {"lat": 13.0358, "lon": 80.1567, "type": "area"}),
    ("Ambattur",           {"lat": 13.1143, "lon": 80.1548, "type": "area"}),
    ("Perambur",           {"lat": 13.1168, "lon": 80.2448, "type": "area"}),
    ("Egmore",             {"lat": 13.0732, "lon": 80.2609, "type": "area"}),
]

_TRIE = Trie()
for name, data in _LOCATIONS:
    _TRIE.insert(name, data)

# Bootstrap graph for connectivity / MST endpoints
_graph_data = generate_city_graph(rows=10, cols=10)
_GRAPH = load_graph_from_dict(_graph_data)


# ── MODELS ────────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    name: str
    lat: float
    lon: float
    type: str


class ConnectivityResponse(BaseModel):
    src: int
    dst: int
    connected: bool
    num_components: int


class MSTResponse(BaseModel):
    num_edges: int
    total_weight: float
    edges: list[dict]


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@router.get("/search", response_model=list[SearchResult])
def search_locations(
    q: str = Query(..., min_length=1, description="Search prefix"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Autocomplete location search using the Trie.
    Returns up to `limit` locations matching the prefix `q`.
    O(k + m) where k = len(q) and m = results returned.
    """
    if not q.strip():
        raise HTTPException(400, "Query cannot be empty")

    results = _TRIE.search_prefix(q.strip(), limit=limit)
    return [
        SearchResult(
            name=r["name"].title(),
            lat=r["lat"],
            lon=r["lon"],
            type=r.get("type", "place"),
        )
        for r in results
    ]


@router.get("/connectivity", response_model=ConnectivityResponse)
def check_connectivity(
    src: int = Query(..., description="Source node ID"),
    dst: int = Query(..., description="Destination node ID"),
):
    """
    Check if two nodes are connected using Union-Find.
    Near O(1) amortized — much faster than BFS/DFS per query.
    """
    uf = UnionFind(_GRAPH.num_nodes)
    for weight, u, v in _GRAPH.all_edges():
        uf.union(u, v)

    return ConnectivityResponse(
        src=src,
        dst=dst,
        connected=uf.connected(src, dst),
        num_components=uf.component_count(),
    )


@router.get("/mst", response_model=MSTResponse)
def get_mst():
    """
    Compute and return the Minimum Spanning Tree using Kruskal's algorithm.
    Useful for infrastructure analysis — the cheapest connected road skeleton.
    """
    edges = _GRAPH.all_edges()
    mst_edges, total_weight = kruskal_mst(_GRAPH.num_nodes, edges)

    return MSTResponse(
        num_edges=len(mst_edges),
        total_weight=round(total_weight, 4),
        edges=[
            {"weight": round(w, 4), "src": u, "dst": v}
            for w, u, v in mst_edges
        ],
    )
