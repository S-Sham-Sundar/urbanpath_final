"""
Search API — /search, /connectivity, /mst
Developer B: Ajith

Trie autocomplete with Redis caching + latency reporting.
"""

import time
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.trie import Trie
from core.kruskal import kruskal_mst
from core.union_find import UnionFind
from core import cache

router = APIRouter()

# ── Bootstrap Trie with 60 Chennai POIs ──────────────────────────────────────

_LOCATIONS = [
    ("Marina Beach",            {"lat": 13.0500, "lon": 80.2824, "type": "beach"}),
    ("Mall of Chennai",         {"lat": 13.0200, "lon": 80.2500, "type": "mall"}),
    ("Mandaveli",               {"lat": 13.0209, "lon": 80.2674, "type": "area"}),
    ("Mount Road",              {"lat": 13.0604, "lon": 80.2496, "type": "road"}),
    ("Mylapore",                {"lat": 13.0368, "lon": 80.2676, "type": "area"}),
    ("Anna Nagar",              {"lat": 13.0850, "lon": 80.2101, "type": "area"}),
    ("Adyar",                   {"lat": 13.0012, "lon": 80.2565, "type": "area"}),
    ("T Nagar",                 {"lat": 13.0418, "lon": 80.2341, "type": "area"}),
    ("Tambaram",                {"lat": 12.9249, "lon": 80.1000, "type": "suburb"}),
    ("Velachery",               {"lat": 12.9815, "lon": 80.2180, "type": "area"}),
    ("Guindy",                  {"lat": 13.0067, "lon": 80.2206, "type": "area"}),
    ("Koyambedu",               {"lat": 13.0694, "lon": 80.1948, "type": "area"}),
    ("Central Station",         {"lat": 13.0827, "lon": 80.2707, "type": "transit"}),
    ("Chennai Airport",         {"lat": 12.9941, "lon": 80.1709, "type": "transit"}),
    ("Santhome",                {"lat": 13.0330, "lon": 80.2771, "type": "area"}),
    ("Besant Nagar",            {"lat": 13.0002, "lon": 80.2683, "type": "area"}),
    ("Porur",                   {"lat": 13.0358, "lon": 80.1567, "type": "area"}),
    ("Ambattur",                {"lat": 13.1143, "lon": 80.1548, "type": "area"}),
    ("Perambur",                {"lat": 13.1168, "lon": 80.2448, "type": "area"}),
    ("Egmore",                  {"lat": 13.0732, "lon": 80.2609, "type": "area"}),
    ("Nungambakkam",            {"lat": 13.0569, "lon": 80.2425, "type": "area"}),
    ("Chromepet",               {"lat": 12.9516, "lon": 80.1462, "type": "area"}),
    ("Pallavaram",              {"lat": 12.9675, "lon": 80.1491, "type": "area"}),
    ("Sholinganallur",          {"lat": 12.9010, "lon": 80.2279, "type": "area"}),
    ("OMR",                     {"lat": 12.9010, "lon": 80.2230, "type": "road"}),
    ("ECR",                     {"lat": 12.8406, "lon": 80.2320, "type": "road"}),
    ("Poonamallee",             {"lat": 13.0467, "lon": 80.0980, "type": "area"}),
    ("Avadi",                   {"lat": 13.1148, "lon": 80.1017, "type": "area"}),
    ("Tondiarpet",              {"lat": 13.1176, "lon": 80.2942, "type": "area"}),
    ("Royapuram",               {"lat": 13.1052, "lon": 80.2942, "type": "area"}),
    ("Washermanpet",            {"lat": 13.1106, "lon": 80.2891, "type": "area"}),
    ("Kodambakkam",             {"lat": 13.0524, "lon": 80.2283, "type": "area"}),
    ("Vadapalani",              {"lat": 13.0525, "lon": 80.2121, "type": "area"}),
    ("Virugambakkam",           {"lat": 13.0627, "lon": 80.1956, "type": "area"}),
    ("Saidapet",                {"lat": 13.0210, "lon": 80.2230, "type": "area"}),
    ("Little Mount",            {"lat": 13.0132, "lon": 80.2189, "type": "landmark"}),
    ("St Thomas Mount",         {"lat": 13.0014, "lon": 80.1709, "type": "landmark"}),
    ("Meenambakkam",            {"lat": 12.9897, "lon": 80.1690, "type": "area"}),
    ("Pallikaranai",            {"lat": 12.9384, "lon": 80.2148, "type": "area"}),
    ("Perungudi",               {"lat": 12.9564, "lon": 80.2417, "type": "area"}),
    ("Thoraipakkam",            {"lat": 12.9337, "lon": 80.2393, "type": "area"}),
    ("Siruseri",                {"lat": 12.8394, "lon": 80.2201, "type": "area"}),
    ("Medavakkam",              {"lat": 12.9183, "lon": 80.1944, "type": "area"}),
    ("Pammal",                  {"lat": 12.9726, "lon": 80.1308, "type": "area"}),
    ("Anakaputhur",             {"lat": 12.9769, "lon": 80.1278, "type": "area"}),
    ("Thiruvottiyur",           {"lat": 13.1561, "lon": 80.3026, "type": "area"}),
    ("Manali",                  {"lat": 13.1699, "lon": 80.2583, "type": "area"}),
    ("Madhavaram",              {"lat": 13.1490, "lon": 80.2326, "type": "area"}),
    ("Kolathur",                {"lat": 13.1253, "lon": 80.2283, "type": "area"}),
    ("Villivakkam",             {"lat": 13.1013, "lon": 80.2172, "type": "area"}),
    ("Korattur",                {"lat": 13.1063, "lon": 80.1949, "type": "area"}),
    ("Pattabiram",              {"lat": 13.1140, "lon": 80.0706, "type": "area"}),
    ("Thirumazhisai",           {"lat": 13.0820, "lon": 80.0710, "type": "area"}),
    ("Nerkundram",              {"lat": 13.0740, "lon": 80.1850, "type": "area"}),
    ("Nandanam",                {"lat": 13.0267, "lon": 80.2389, "type": "area"}),
    ("Alwarpet",                {"lat": 13.0318, "lon": 80.2545, "type": "area"}),
    ("Teynampet",               {"lat": 13.0414, "lon": 80.2500, "type": "area"}),
    ("Chetpet",                 {"lat": 13.0694, "lon": 80.2418, "type": "area"}),
    ("Kilpauk",                 {"lat": 13.0823, "lon": 80.2327, "type": "area"}),
    ("Purasawalkam",            {"lat": 13.0876, "lon": 80.2594, "type": "area"}),
]

_TRIE = Trie()
for _name, _data in _LOCATIONS:
    _TRIE.insert(_name, _data)


# ── Models ────────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    name: str
    lat: float
    lon: float
    type: str
    latency_ms: float = 0.0


class ConnectivityResponse(BaseModel):
    src: int
    dst: int
    connected: bool
    num_components: int
    latency_ms: float = 0.0


class MSTResponse(BaseModel):
    num_edges: int
    total_weight: float
    edges: list[dict]
    latency_ms: float = 0.0


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/search", response_model=list[SearchResult])
def search_locations(
    q: str = Query(..., min_length=1, description="Search prefix"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Trie autocomplete — O(k) prefix lookup, Redis-cached, latency reported.
    """
    if not q.strip():
        raise HTTPException(400, "Query cannot be empty")

    cache_key = cache.make_key("search", q.strip().lower(), limit)
    cached = cache.get(cache_key)
    if cached:
        return cached

    t0 = time.perf_counter()
    results = _TRIE.search_prefix(q.strip(), limit=limit)
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    out = [
        SearchResult(
            name=r["name"].title(),
            lat=r["lat"],
            lon=r["lon"],
            type=r.get("type", "place"),
            latency_ms=latency_ms,
        ).model_dump()
        for r in results
    ]
    cache.set(cache_key, out, ttl=300)
    return out


@router.get("/connectivity", response_model=ConnectivityResponse)
def check_connectivity(
    src: int = Query(..., description="Source node index"),
    dst: int = Query(..., description="Destination node index"),
):
    """
    Union-Find connectivity check — near O(1) amortized.
    """
    from api.main import GRAPH   # lazy import to avoid circular

    t0 = time.perf_counter()
    n = GRAPH.node_count()
    uf = UnionFind(n)
    for from_id, to_id, w in GRAPH.all_edges():
        u = GRAPH.index_of(from_id)
        v = GRAPH.index_of(to_id)
        if u >= 0 and v >= 0:
            uf.union(u, v)
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    return ConnectivityResponse(
        src=src,
        dst=dst,
        connected=uf.connected(src, dst),
        num_components=uf.component_count(),
        latency_ms=latency_ms,
    )


@router.get("/mst", response_model=MSTResponse)
def get_mst():
    """
    Kruskal's MST — O(E log E).
    """
    from api.main import GRAPH

    cache_key = cache.make_key("mst", GRAPH.node_count())
    cached = cache.get(cache_key)
    if cached:
        return cached

    t0 = time.perf_counter()
    raw_edges = [(w, GRAPH.index_of(u), GRAPH.index_of(v))
                 for u, v, w in GRAPH.all_edges()
                 if GRAPH.index_of(u) >= 0 and GRAPH.index_of(v) >= 0]
    mst_edges, total_weight = kruskal_mst(GRAPH.node_count(), raw_edges)
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    result = MSTResponse(
        num_edges=len(mst_edges),
        total_weight=round(total_weight, 4),
        edges=[{"weight": round(w, 4), "src": u, "dst": v} for w, u, v in mst_edges],
        latency_ms=latency_ms,
    ).model_dump()
    cache.set(cache_key, result, ttl=3600)
    return result
