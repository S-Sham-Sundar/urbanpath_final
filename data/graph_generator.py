"""
UrbanPath — Graph loader (Dev A · Sham)

Priority:
  1. Real OpenStreetMap data  →  data/chennai_graph.json  (run download_osm.py once)
  2. Synthetic fallback grid  →  used during development / CI

The OSM graph gives 50K+ real Chennai road nodes with actual lat/lon and
road names. The synthetic graph is a uniform grid for algorithm testing.
"""

import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.graph import Edge, Graph, Node, haversine

OSM_PATH = os.path.join(os.path.dirname(__file__), "chennai_graph.json")


# ── OSM loader ────────────────────────────────────────────────────────────────

def load_graph_from_osm(path: str = OSM_PATH) -> Graph:
    """Load real Chennai road network from pre-downloaded OSM JSON."""
    with open(path) as f:
        data = json.load(f)

    g = Graph()
    for nid, n in data["nodes"].items():
        g.add_node(Node(str(nid), float(n["lat"]), float(n["lon"]), n.get("name", "")))

    for e in data["edges"]:
        g.add_edge(Edge(str(e["from"]), str(e["to"]), float(e["weight"]), e.get("name", "")))

    return g


# ── Synthetic fallback ────────────────────────────────────────────────────────

def generate_city_graph(
    rows: int = 32,
    cols: int = 32,
    origin_lat: float = 13.0500,
    origin_lon: float = 80.2100,
) -> Graph:
    """
    Synthetic grid graph centred on Chennai.
    Default 32×32 = 1 024 nodes with ~1.1 km spacing.
    Used when OSM data hasn't been downloaded yet.
    """
    g = Graph()
    spacing = 0.009   # ≈ 1 km

    node_ids: dict = {}
    for r in range(rows):
        for c in range(cols):
            nid = str(r * cols + c)
            lat = origin_lat + r * spacing
            lon = origin_lon + c * spacing
            g.add_node(Node(nid, lat, lon, f"Intersection {nid}"))
            node_ids[(r, c)] = nid

    rng = random.Random(42)
    for r in range(rows):
        for c in range(cols):
            nid = node_ids[(r, c)]
            n = g.nodes[nid]
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in node_ids:
                    nbr_id = node_ids[(nr, nc)]
                    nb = g.nodes[nbr_id]
                    w = haversine(n.lat, n.lon, nb.lat, nb.lon)
                    w *= rng.uniform(1.0, 1.4)   # road-tortuosity factor
                    g.add_edge(Edge(nid, nbr_id, round(w, 5)))

    return g


# ── Public entry point ────────────────────────────────────────────────────────

def get_graph() -> Graph:
    """Return the best available graph (OSM preferred, synthetic fallback)."""
    if os.path.exists(OSM_PATH):
        print(f"[graph] Loading OSM Chennai graph from {OSM_PATH} …")
        g = load_graph_from_osm()
        print(f"[graph] {g.node_count():,} nodes  |  {g.edge_count():,} edges  (OpenStreetMap)")
        return g

    print("[graph] OSM data not found — using 1 024-node synthetic graph.")
    print("[graph] For real Chennai data run:  python3 data/download_osm.py")
    return generate_city_graph()


def load_graph_from_dict(data: dict) -> Graph:
    """Deserialise a graph from a plain dict (used in tests / API)."""
    g = Graph()
    for n in data.get("nodes", []):
        g.add_node(Node(n["id"], n["lat"], n["lon"], n.get("name", "")))
    for e in data.get("edges", []):
        g.add_edge(Edge(e["from"], e["to"], e["weight"], e.get("name", "")))
    return g
