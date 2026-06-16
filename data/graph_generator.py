"""
Graph Generator — Synthetic City Graph for Development & Testing
Developer A: Sham

Generates a realistic road network for Chennai (or any bounding box)
without requiring a live OpenStreetMap API call during development.

The generated graph approximates a grid-with-noise layout:
  - Grid intersections with random lat/lon offsets (realistic jitter)
  - Edge weights = Haversine distance × traffic multiplier
  - Traffic multiplier drawn from a realistic distribution

For production, replace with OSM data loader.
"""

import math
import random


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def generate_city_graph(
    rows: int = 10,
    cols: int = 10,
    lat_origin: float = 13.00,
    lon_origin: float = 80.20,
    lat_step: float = 0.012,
    lon_step: float = 0.014,
    seed: int = 42,
) -> dict:
    """
    Generate a synthetic city graph as a dictionary with nodes and edges.

    Returns
    -------
    {
        "nodes": [{id, lat, lon, name}, ...],
        "edges": [{src, dst, weight, road_name}, ...]
    }
    """
    rng = random.Random(seed)
    nodes = []
    edges = []

    node_id = 0
    grid = {}   # (r, c) -> node_id

    # Place nodes on a jittered grid
    for r in range(rows):
        for c in range(cols):
            lat = lat_origin + r * lat_step + rng.uniform(-0.002, 0.002)
            lon = lon_origin + c * lon_step + rng.uniform(-0.002, 0.002)
            nodes.append({
                "id": node_id,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "name": f"Intersection_{r}_{c}",
            })
            grid[(r, c)] = node_id
            node_id += 1

    # Connect grid neighbours (right and down), plus a few diagonal shortcuts
    for r in range(rows):
        for c in range(cols):
            uid = grid[(r, c)]
            u_node = nodes[uid]

            # Right neighbour
            if c + 1 < cols:
                vid = grid[(r, c + 1)]
                v_node = nodes[vid]
                dist = _haversine(u_node["lat"], u_node["lon"], v_node["lat"], v_node["lon"])
                traffic = rng.uniform(1.0, 2.5)
                edges.append({
                    "src": uid, "dst": vid,
                    "weight": round(dist * traffic, 4),
                    "road_name": f"H_Road_{r}_{c}",
                })

            # Down neighbour
            if r + 1 < rows:
                vid = grid[(r + 1, c)]
                v_node = nodes[vid]
                dist = _haversine(u_node["lat"], u_node["lon"], v_node["lat"], v_node["lon"])
                traffic = rng.uniform(1.0, 2.5)
                edges.append({
                    "src": uid, "dst": vid,
                    "weight": round(dist * traffic, 4),
                    "road_name": f"V_Road_{r}_{c}",
                })

    return {"nodes": nodes, "edges": edges}


def load_graph_from_dict(data: dict):
    """Convert the generated dict into a Graph object."""
    from core.graph import Graph
    g = Graph()
    for n in data["nodes"]:
        g.add_node(n["id"], n["lat"], n["lon"], n["name"])
    for e in data["edges"]:
        g.add_edge(e["src"], e["dst"], e["weight"],
                   bidirectional=True, road_name=e["road_name"])
    return g


if __name__ == "__main__":
    data = generate_city_graph(rows=5, cols=5)
    print(f"Nodes: {len(data['nodes'])}, Edges: {len(data['edges'])}")
    g = load_graph_from_dict(data)
    print(g)
