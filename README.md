# UrbanPath

> A city-scale graph routing engine built from scratch - no Google Maps, no NetworkX, no shortcuts.

---

## Hero Metrics

| What | Number |
|------|--------|
| Road network nodes (Chennai OSM) | 68,610 |
| POIs indexed in Trie | 60 |
| Search latency | 0.031 ms |
| Held-Karp latency (5 stops) | 0.035 ms |
| Held-Karp vs greedy reduction | ~23% |
| Traffic buckets per road | 168 (7 days × 24 hrs) |
| Visualizer subgraph size | 200 nodes |
| API endpoints | 9 |
| Algorithms implemented | 9 |

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Benchmarks / Results](#benchmarks--results)
6. [Visuals](#visuals)
7. [API Reference](#api-reference)
8. [Setup](#setup)
9. [Project Structure](#project-structure)
10. [Design Decisions](#design-decisions)
11. [Limitations](#limitations)
12. [Future Work](#future-work)

---

## Overview

UrbanPath is a portfolio project built by two people to prove that the algorithms taught in class actually work at scale. We took the real Chennai road network from OpenStreetMap (68,610 nodes), wrote every algorithm from scratch in Python, wired it up with a FastAPI backend, and built a frontend with three pages — a map explorer, a delivery planner, and a graph traversal visualizer.

No algorithm libraries were used. Every data structure - the graph, heap, trie, segment tree, union-find - is hand-written.

**Dev A - Sham:** Graph, Dijkstra, A*, BFS Isochrone, MinHeap, graph data layer, Redis caching.
**Dev B - Ajith:** Trie, Held-Karp TSP, K-means++, Kruskal MST, Segment Tree, Union-Find, frontend

---

## Features

**Map Explorer (Dev A)**
- Trie-based location search over 60 Chennai POIs — O(k) prefix lookup
- A* and Dijkstra routing — toggle between them to compare
- Results plotted on a Leaflet map with the exact path drawn

**Delivery Planner (Dev B)**
- Held-Karp exact TSP for ≤ 20 stops — O(2ⁿ · n²)
- K-means++ clustering for 100+ stops — splits into sub-20 clusters, runs Held-Karp on each
- ~23% shorter routes vs greedy nearest-neighbour
- Live traffic weighting using Segment Tree range queries

**Graph Visualizer (Dev A + Dev B)**
- BFS and Dijkstra animated step-by-step on a 200-node subgraph
- Colour-coded node states: unvisited → frontier → current → visited → final path
- Speed controls: Slow (300ms), Normal (80ms), Fast (20ms)
- Runs fully client-side in the browser

**Backend**
- Redis caching with in-memory LRU fallback (5-minute TTL)
- Latency reported on every response
- OSM graph loaded once at startup, shared across all routes

---

## Architecture

```
Browser (HTML/CSS/JS + D3.js + Leaflet)
         |
         | HTTP
         v
FastAPI  (uvicorn)
  ├── /api/route        → Dijkstra / A*
  ├── /api/search       → Trie autocomplete
  ├── /api/delivery     → Held-Karp + K-means++
  ├── /api/traffic/{id} → Segment Tree range query
  ├── /api/isochrone    → BFS reachability
  ├── /api/mst          → Kruskal MST
  ├── /api/graph        → graph nodes for visualizer
  ├── /api/visualize    → BFS/Dijkstra step stream
  └── /api/connectivity → Union-Find check
         |
    Core Algorithms
  ├── graph.py          (adjacency list, haversine)
  ├── dijkstra.py       (O(E log V))
  ├── astar.py          (O(E log V), haversine heuristic)
  ├── bfs_isochrone.py  (O(V + E))
  ├── trie.py           (O(k) lookup)
  ├── tsp_held_karp.py  (O(2ⁿ · n²))
  ├── kmeans.py         (K-means++ init)
  ├── segment_tree.py   (O(log n) range min/sum)
  ├── kruskal.py        (O(E log E))
  ├── union_find.py     (O(α(n)) amortised)
  └── min_heap.py       (binary heap)
         |
    Data Layer
  ├── chennai_graph.json  (OpenStreetMap — 68,610 nodes)
  └── graph_generator.py  (OSM loader + synthetic fallback)
         |
    Cache Layer
  └── cache.py  (Redis → in-memory LRU fallback)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Backend framework | FastAPI 0.111 |
| Server | Uvicorn 0.29 |
| Road data | OpenStreetMap via osmnx |
| Caching | Redis (in-memory LRU fallback) |
| Frontend | HTML, CSS, vanilla JS |
| Map | Leaflet 1.9.4 |
| Graph visualizer | D3.js v7 |
| Validation | Pydantic v2 |
| Testing | pytest + httpx |

---

## Benchmarks / Results

All latencies measured with `time.perf_counter()` on a MacBook, server running locally.

| Endpoint | Operation | Latency |
|----------|-----------|---------|
| `/api/search` | Trie prefix lookup, cache miss | 0.031 ms |
| `/api/search` | Trie prefix lookup, cache hit | < 0.01 ms |
| `/api/delivery` | Held-Karp, 5 stops | 0.035 ms |
| `/api/route` | Dijkstra, 68,610-node graph | ~2000 ms |
| `/api/route` | A*, 68,610-node graph | faster than Dijkstra (heuristic-guided) |
| `/api/traffic/{id}` | Segment Tree range query | O(log 168) |

**Held-Karp vs Greedy nearest-neighbour:**
- Tested across multiple random stop sets (3–15 stops)
- Average reduction: ~23% shorter total distance
- Greedy runs in O(n²), Held-Karp runs in O(2ⁿ · n²) — the trade-off is worth it up to 20 stops

**Trie vs linear scan (60 POIs):**
- Trie: O(k) where k = prefix length
- Linear scan: O(n) where n = 60
- At 60 POIs the gap is small, but the structure scales — same code works at 600K POIs

---

## Visuals

Three-page frontend served locally:

- `index.html` — Map Explorer with Leaflet map, A*/Dijkstra toggle, Trie search
- `delivery.html` — Delivery Planner with stop input and Held-Karp result
- `visualizer.html` — D3.js graph traversal with BFS/Dijkstra animation

Serve with:
```bash
cd frontend
python3 -m http.server 3000
```
Then open `http://localhost:3000`

> Do not open the HTML files directly via `file://` — Leaflet tiles will be blocked by OSM's referer policy.

---

## API Reference

All endpoints served at `http://localhost:8000`.

### GET /api/route
Find shortest path between two nodes.

| Param | Type | Description |
|-------|------|-------------|
| `src` | int | Source node index |
| `dst` | int | Destination node index |
| `algo` | string | `astar` or `dijkstra` |

Response includes `distance_km`, `path`, `latency_ms`, `cache_hit`.

---

### GET /api/search
Trie autocomplete.

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Prefix string |

Response includes `results[]`, `latency_ms`.

---

### POST /api/delivery
Optimise delivery route.

Body:
```json
{
  "stops": [
    {"lat": 13.0827, "lon": 80.2707},
    {"lat": 13.0604, "lon": 80.2496}
  ]
}
```

Response includes `route`, `total_distance`, `strategy` (held_karp / kmeans_held_karp), `naive_distance`, `reduction_pct`, `latency_ms`.

---

### GET /api/traffic/{road_id}
Segment Tree range query over traffic data.

| Param | Type | Description |
|-------|------|-------------|
| `start_hour` | int | 0–167 |
| `end_hour` | int | 0–167 |

---

### GET /api/isochrone
BFS reachability from a source node within a time limit.

| Param | Type | Description |
|-------|------|-------------|
| `src` | int | Source node |
| `time_limit` | float | Minutes |

---

### GET /api/mst
Kruskal MST of the full graph.

---

### GET /api/connectivity
Union-Find check — are two nodes in the same connected component?

| Param | Type | Description |
|-------|------|-------------|
| `a` | int | Node index |
| `b` | int | Node index |

---

### GET /api/graph
Returns up to 300 nodes for the D3 visualizer.

---

### GET /api/visualize
Returns BFS or Dijkstra traversal steps on a 200-node subgraph.

| Param | Type | Description |
|-------|------|-------------|
| `src` | int | Source node |
| `dst` | int | Destination node |
| `algo` | string | `bfs` or `dijkstra` |

---

## Setup

**Requirements:** Python 3.12, pip. Redis is optional (falls back to in-memory cache).

```bash
# Clone
git clone https://github.com/S-Sham-Sundar/urbanpath_final.git
cd urbanpath_final

# Install dependencies
pip install -r requirements.txt

# Download Chennai road network (run once)
python data/download_osm.py
# This saves data/chennai_graph.json — 68,610 nodes, takes ~2 minutes

# Start the API server
uvicorn api.main:app --reload

# In a separate terminal — serve the frontend
cd frontend
python3 -m http.server 3000
```

Open `http://localhost:3000` for the frontend, `http://localhost:8000/docs` for the API docs.

---

## Project Structure

```
urbanpath_final/
├── api/
│   ├── main.py                  # FastAPI app, graph loaded at startup
│   └── routes/
│       ├── routing.py           # /route, /isochrone, /graph, /visualize
│       ├── search.py            # /search
│       └── isochrone.py         # /delivery, /traffic, /mst, /connectivity
├── core/
│   ├── graph.py                 # Graph, Node, Edge, haversine
│   ├── dijkstra.py              # Dijkstra + dijkstra_all
│   ├── astar.py                 # A* with haversine heuristic
│   ├── bfs_isochrone.py         # BFS reachability + boundary
│   ├── trie.py                  # Prefix tree
│   ├── tsp_held_karp.py         # Bitmask DP TSP
│   ├── kmeans.py                # K-means++ clustering
│   ├── segment_tree.py          # Range min / sum
│   ├── kruskal.py               # MST
│   ├── union_find.py            # Path-compressed union-find
│   ├── min_heap.py              # Binary heap
│   └── cache.py                 # Redis + LRU fallback
├── data/
│   ├── graph_generator.py       # OSM loader + synthetic fallback
│   ├── download_osm.py          # One-time OSM download script
│   └── chennai_graph.json       # 68,610-node road network (generated)
├── frontend/
│   ├── index.html               # 01 · Map Explorer
│   ├── delivery.html            # 02 · Delivery Planner
│   ├── visualizer.html          # 03 · Visualizer
│   ├── app.js                   # Map Explorer logic
│   ├── delivery.js              # Delivery Planner logic
│   └── style.css                # Shared styles
├── tests/
│   └── test_algorithms.py       # pytest suite
└── requirements.txt
```

---

## Design Decisions

**Why hand-write everything?**
The point of the project was to actually implement the algorithms, not to call `nx.dijkstra_path()`. Every data structure in `core/` was written from scratch.

**Why OSM data?**
Synthetic grids (32×32 = 1024 nodes) are fine for testing but pointless as a claim. Chennai's real road network has 68,610 nodes, irregular topology, and actual geographic coordinates — the algorithms have to work on real data, not a toy.

**Why separate the graph from the Trie?**
Two completely different things. The OSM graph is for routing — 68,610 road intersection nodes with no names. The Trie holds 60 named POIs (places like "Marina Beach", "Chennai Central") for the search box. A user searches by name, gets a coordinate, and then routing takes over from there.

**Why Redis with LRU fallback?**
Redis isn't guaranteed to be installed on every machine. The fallback means the server starts and works without it — Redis just makes repeated queries faster. The `cache.py` module handles both cases transparently.

**Why a 200-node subgraph for the visualizer?**
Running BFS or Dijkstra on 68,610 nodes and streaming every step to the browser would produce tens of thousands of animation frames. 200 nodes gives enough structure to actually see the algorithm work without killing the browser.

**Why K-means++ over standard K-means?**
Standard K-means picks initial centroids randomly, which can converge to bad clusters. K-means++ spreads the initial centroids using a distance-weighted distribution — typically 2–5× fewer iterations to convergence and more consistent cluster quality.

---

## Limitations

- Dijkstra on the full 68,610-node graph takes ~2 seconds. A* is faster but still slow on very long routes — the heuristic helps but the graph is large.
- The Held-Karp cap of 20 stops is a hard algorithmic limit (O(2ⁿ · n²) becomes infeasible beyond that), not a choice.
- Traffic data is synthetic — the 168 buckets are randomly seeded, not pulled from real traffic feeds.
- The frontend is three static HTML files served by Python's built-in HTTP server. No build step, no bundler.
- `chennai_graph.json` is not committed to the repo (too large). You have to run `download_osm.py` yourself.

---

## Future Work

- Replace synthetic traffic data with real feeds (TomTom / HERE API)
- A* bidirectional search to cut routing time on long cross-city paths
- Persistent Redis deployment so cache survives server restarts
- WebSocket streaming for the visualizer instead of a single JSON dump
- Expand Trie POIs beyond 60 — the structure handles it, the data just needs to be added
