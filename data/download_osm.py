"""
UrbanPath — One-time Chennai OSM Data Downloader
=================================================
Run this ONCE to download Chennai's real road network from OpenStreetMap.
Saves to data/chennai_graph.json (~30–60 MB, takes ~2–4 minutes).

Usage:
    pip3 install osmnx --break-system-packages
    python3 data/download_osm.py
"""

import json
import os
import time

OUTPUT = os.path.join(os.path.dirname(__file__), "chennai_graph.json")


def download():
    try:
        import osmnx as ox
    except ImportError:
        print("osmnx not installed. Run:")
        print("  pip3 install osmnx --break-system-packages")
        return

    print("=" * 55)
    print("  UrbanPath — Chennai OSM Road Network Downloader")
    print("=" * 55)
    print("\nDownloading Chennai road network from OpenStreetMap...")
    print("This takes ~2–4 minutes. Please wait.\n")

    t0 = time.time()
    G = ox.graph_from_place(
        "Chennai, Tamil Nadu, India",
        network_type="drive",
        simplify=True,
    )
    elapsed = time.time() - t0

    print(f"Downloaded in {elapsed:.1f}s")
    print(f"Nodes : {len(G.nodes):,}")
    print(f"Edges : {len(G.edges):,}")

    print("\nConverting to JSON format...")
    nodes = {}
    for osmid, data in G.nodes(data=True):
        nodes[str(osmid)] = {
            "id": str(osmid),
            "lat": data["y"],
            "lon": data["x"],
            "name": data.get("name", ""),
        }

    edges = []
    seen = set()
    for u, v, data in G.edges(data=True):
        key = (str(u), str(v))
        if key in seen:
            continue
        seen.add(key)
        length_m = data.get("length", 0)
        edges.append({
            "from": str(u),
            "to": str(v),
            "weight": round(length_m / 1000, 5),   # km
            "name": data.get("name", "") if isinstance(data.get("name"), str) else "",
            "highway": data.get("highway", "") if isinstance(data.get("highway"), str) else "",
        })

    graph_data = {
        "city": "Chennai",
        "source": "OpenStreetMap",
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }

    print(f"Saving to {OUTPUT} ...")
    with open(OUTPUT, "w") as f:
        json.dump(graph_data, f)

    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"\nDone!  {size_mb:.1f} MB saved.")
    print(f"Graph: {len(nodes):,} nodes, {len(edges):,} edges")
    print("\nRestart the server:")
    print("  python3 -m uvicorn api.main:app --reload")


if __name__ == "__main__":
    download()
