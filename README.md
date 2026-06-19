# UrbanPath

A city-scale graph routing engine built from scratch - no Google Maps, no NetworkX, no shortcuts.

---

## Hero Metrics

| What | Number |
|------|--------|
| Road network nodes (Chennai OSM) | 68,610 |
| POIs indexed in Trie | 60 |
| Search latency | 0.031 ms |
| Held-Karp latency (5 stops) | 0.035 ms |
| Held-Karp vs greedy reduction | ~23% |
| Traffic buckets per road | 168 (7 days x 24 hrs) |
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

UrbanPath is a portfolio project built by two people to prove that the algorithms taught in class actually work at scale. We took the real Chennai road network from OpenStreetMap (68,610 nodes), wrote every algorithm from scratch in Python, wired it up with a FastAPI backend, and built a frontend with three pages - a map explorer, a delivery planner, and a graph traversal visualizer.

No algorithm libraries were used. Every data structure - the graph, heap, trie, segment tree, union-find - is hand-written.

**Dev A - Sham:** Graph data structure (adjacency list, haversine), MinHeap (binary heap from scratch), Dijkstra shortest path, A* with Haversine heuristic, BFS isochrone (reachability within a time budget), FastAPI app setup and graph loading at startup, all routing API routes (/route, /isochrone, /graph, /visualize), visualizer step-frame backend, Redis caching layer with in-memory LRU fallback, PostgreSQL schema design (nodes, edges, path_cache tables), OSM data loader and synthetic graph generator. ~10 files, ~600-800 lines of Python.

**Dev B - Ajith:** Trie prefix tree (O(k) autocomplete), Held-Karp TSP (bitmask DP, exact optimal), K-means++ clustering (for large stop sets), Kruskal MST (with Union-Find), Segment Tree (traffic range queries), Union-Find (DSU, path-compressed), all search/delivery/traffic/MST/connectivity API routes, and the complete frontend - three HTML pages with Leaflet map, D3.js visualizer, search bar, route panel, traffic overlay, and shared CSS. ~17 files, ~1000-1200 lines.

---

## Features

### Map Explorer

**Dev A - routing backend:**
- Dijkstra and A* running on the full 68,610-node Chennai graph
- A* uses a Haversine heuristic (straight-line distance over the curve of the Earth) to lean toward the goal and explore far fewer nodes than Dijkstra - same optimal answer, less digging
- BFS isochrone - "where can I reach from this point within N minutes?" - floods outward by travel time and cuts off at the budget
- Every route query goes through Redis cache first; repeated queries return instantly with a `cache_hit` flag in the response. Falls back to an in-memory LRU cache if Redis is not installed.

**Dev B - search and frontend:**
- Trie-based location search over 60 Chennai POIs - O(k) prefix lookup where k is the length of the typed prefix
- Leaflet map with the exact path drawn as a polyline on the real Chennai road layout
- Search bar with autocomplete, A*/Dijkstra toggle, and a result panel showing distance and latency

---

### Delivery Planner (Dev B)

- Held-Karp exact TSP for up to 20 stops - O(2^n * n^2) bitmask DP, guaranteed to find the shortest visiting order
- K-means++ clustering for 100+ stops - splits into sub-20 clusters, runs Held-Karp on each cluster independently
- ~23% shorter routes on average compared to greedy nearest-neighbour
- Live traffic weighting via Segment Tree range queries over 168 hourly traffic buckets (7 days x 24 hours per road)

---

### Graph Visualizer (Dev A + Dev B)

**Dev A - algorithm backend:**
- BFS and Dijkstra traversal recorded as a sequence of step-frames during execution
- Each frame captures: current node, newly discovered nodes, frontier queue, and full visited set at that moment
- Same traversal code as the routing engine - the frames come from the live algorithm, not a pre-baked demo
- Runs on a 200-node subgraph to keep frame count and browser memory manageable

**Dev B - animation frontend:**
- D3.js renders each frame with colour-coded node states: unvisited, frontier, current, visited, final path
- Speed controls: Slow (300ms), Normal (80ms), Fast (20ms) per frame
- Runs fully client-side - no server round-trips during playback once the frames are loaded

---

### Backend Infrastructure (Dev A)

- `api/main.py` - FastAPI app that loads the full Chennai graph once at startup and shares it across all route handlers
- `core/cache.py` - Redis client with an in-memory LRU fallback. The server starts and works with or without Redis installed.
- PostgreSQL schema - nodes table, edges table, path_cache table - designed to support persistent storage of the road network and cached route results
- Latency reported on every API response using `time.perf_counter()`

---

## Architecture

```
Browser (HTML / CSS / vanilla JS - Leaflet, D3.js)     - Dev B
         |
         | HTTP
         v
FastAPI  (uvicorn)                                      - Dev A setup
         |
         +-- /api/route          Dijkstra / A*          (Dev A)
         +-- /api/isochrone      BFS reachability       (Dev A)
         +-- /api/graph          graph nodes dump       (Dev A)
         +-- /api/visualize      BFS/Dijkstra frames    (Dev A)
         +-- /api/search         Trie autocomplete      (Dev B)
         +-- /api/delivery       Held-Karp + K-means++  (Dev B)
         +-- /api/traffic/{id}   Segment Tree query     (Dev B)
         +-- /api/mst            Kruskal MST            (Dev B)
         +-- /api/connectivity   Union-Find check       (Dev B)
         |
    Core Algorithms
         |
         +-- Dev A
         |   +-- graph.py           adjacency list, haversine distance
         |   +-- min_heap.py        binary heap, push/pop O(log n)
         |   +-- dijkstra.py        O(E log V)
         |   +-- astar.py           O(E log V), haversine heuristic
         |   +-- bfs_isochrone.py   O(V + E), time-budgeted flood fill
         |   +-- cache.py           Redis + in-memory LRU fallback
         |
         +-- Dev B
             +-- trie.py            prefix tree, O(k) lookup
             +-- tsp_held_karp.py   bitmask DP TSP, O(2^n * n^2)
             +-- kmeans.py          K-means++ initialisation
             +-- segment_tree.py    range min/sum, O(log n)
             +-- kruskal.py         MST, O(E log E)
             +-- union_find.py      path-compressed DSU, O(alpha(n))
         |
    Data Layer                                          (Dev A)
         +-- graph_generator.py    OSM loader + synthetic grid fallback
         +-- download_osm.py       one-time OSM download script
         +-- chennai_graph.json    68,610-node road network (generated)
         +-- PostgreSQL schema     nodes, edges, path_cache tables
         |
    Cache Layer                                         (Dev A)
         +-- cache.py              Redis primary, in-memory LRU fallback
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
| Database schema | PostgreSQL |
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

**A* vs Dijkstra (Dev A):**
- Both return the same optimal path
- A* uses the Haversine straight-line distance to the goal as a heuristic, so it explores far fewer nodes on a large city graph
- The heuristic never over-estimates (it is admissible), which is the mathematical condition that guarantees the same optimal result

**Held-Karp vs greedy nearest-neighbour (Dev B):**
- Tested across multiple random stop sets (3-15 stops)
- Average reduction: ~23% shorter total distance
- Greedy runs in O(n^2), Held-Karp runs in O(2^n * n^2) - the trade-off is worth it up to 20 stops

**Trie vs linear scan - 60 POIs (Dev B):**
- Trie: O(k) where k is the prefix length typed
- Linear scan: O(n) where n = 60
- At 60 POIs the gap is small, but the structure scales - the same code handles 600K POIs without changes

---

## Visuals

Three-page frontend served locally - all built by Dev B:

- `index.html` - Map Explorer: Leaflet map, A*/Dijkstra toggle, Trie search bar
- `delivery.html` - Delivery Planner: stop input form and Held-Karp result display
- `visualizer.html` - Graph Traversal: D3.js BFS/Dijkstra animation with speed controls

Serve with:

```bash
cd frontend
python3 -m http.server 3000
```

Then open `http://localhost:3000`

> Do not open the HTML files directly via `file://` - Leaflet tiles will be blocked by OSM's referer policy.

---

## API Reference

All endpoints served at `http://localhost:8000`.

---

### GET /api/route - (Dev A)

Find the shortest path between two nodes.

| Param | Type | Description |
|-------|------|-------------|
| `src` | int | Source node index |
| `dst` | int | Destination node index |
| `algo` | string | `astar` or `dijkstra` |

Response includes `distance_km`, `path`, `latency_ms`, `cache_hit`.

---

### GET /api/isochrone - (Dev A)

BFS reachability - all nodes reachable from a source within a time budget.

| Param | Type | Description |
|-------|------|-------------|
| `src` | int | Source node |
| `time_limit` | float | Time budget in minutes |

---

### GET /api/graph - (Dev A)

Returns up to 300 nodes for the D3 visualizer to render.

---

### GET /api/visualize - (Dev A)

Returns BFS or Dijkstra traversal as a sequence of step-frames on a 200-node subgraph.

| Param | Type | Description |
|-------|------|-------------|
| `src` | int | Source node |
| `dst` | int | Destination node |
| `algo` | string | `bfs` or `dijkstra` |

---

### GET /api/search - (Dev B)

Trie prefix autocomplete over 60 Chennai POIs.

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Prefix string |

Response includes `results[]`, `latency_ms`.

---

### POST /api/delivery - (Dev B)

Optimise a multi-stop delivery route.

Body:

```json
{
  "stops": [
    {"lat": 13.0827, "lon": 80.2707},
    {"lat": 13.0604, "lon": 80.2496}
  ]
}
```

Response includes `route`, `total_distance`, `strategy` (held_karp or kmeans_held_karp), `naive_distance`, `reduction_pct`, `latency_ms`.

---

### GET /api/traffic/{road_id} - (Dev B)

Segment Tree range query over hourly traffic data for a road.

| Param | Type | Description |
|-------|------|-------------|
| `start_hour` | int | 0-167 |
| `end_hour` | int | 0-167 |

---

### GET /api/mst - (Dev B)

Kruskal MST of the full graph.

---

### GET /api/connectivity - (Dev B)

Union-Find check - are two nodes in the same connected component?

| Param | Type | Description |
|-------|------|-------------|
| `a` | int | Node index |
| `b` | int | Node index |

---

## Setup

**Requirements:** Python 3.12, pip. Redis is optional - the server falls back to in-memory cache automatically.

```bash
# Clone
git clone https://github.com/S-Sham-Sundar/urbanpath_final.git
cd urbanpath_final

# Install dependencies
pip install -r requirements.txt

# Download Chennai road network (run once - takes ~2 minutes)
python data/download_osm.py
# Saves data/chennai_graph.json - 68,610 nodes

# Start the API server
uvicorn api.main:app --reload

# In a separate terminal - serve the frontend
cd frontend
python3 -m http.server 3000
```

Open `http://localhost:3000` for the frontend, `http://localhost:8000/docs` for interactive API docs.

---

## Project Structure

```
urbanpath_final/
|
+-- api/
|   +-- main.py                    # FastAPI app, graph loaded once at startup    (Dev A)
|   +-- routes/
|       +-- routing.py             # /route (Dijkstra/A*), /graph, /visualize    (Dev A)
|       +-- isochrone.py           # /isochrone (BFS reachability)                (Dev A)
|       +-- search.py              # /search (Trie autocomplete)                  (Dev B)
|       +-- delivery.py            # /delivery (Held-Karp + K-means++)            (Dev B)
|       +-- traffic.py             # /traffic (Segment Tree range query)          (Dev B)
|       +-- mst.py                 # /mst (Kruskal)                               (Dev B)
|       +-- connectivity.py        # /connectivity (Union-Find)                   (Dev B)
|
+-- core/
|   +-- graph.py                   # Graph, adjacency list, haversine             (Dev A)
|   +-- min_heap.py                # Binary heap - push/pop O(log n)             (Dev A)
|   +-- dijkstra.py                # Dijkstra + dijkstra_all                      (Dev A)
|   +-- astar.py                   # A* with Haversine heuristic                 (Dev A)
|   +-- bfs_isochrone.py           # BFS reachability + boundary                 (Dev A)
|   +-- cache.py                   # Redis + in-memory LRU fallback              (Dev A)
|   +-- trie.py                    # Prefix tree, O(k) lookup                    (Dev B)
|   +-- tsp_held_karp.py           # Bitmask DP TSP, O(2^n * n^2)               (Dev B)
|   +-- kmeans.py                  # K-means++ clustering                        (Dev B)
|   +-- segment_tree.py            # Range min/sum, O(log n)                     (Dev B)
|   +-- kruskal.py                 # MST, O(E log E)                             (Dev B)
|   +-- union_find.py              # Path-compressed DSU, O(alpha(n))            (Dev B)
|
+-- data/                                                                         (Dev A)
|   +-- graph_generator.py         # OSM loader + synthetic grid fallback
|   +-- download_osm.py            # One-time OSM download script
|   +-- chennai_graph.json         # 68,610-node road network (generated, not committed)
|
+-- frontend/                                                                     (Dev B)
|   +-- index.html                 # Map Explorer
|   +-- delivery.html              # Delivery Planner
|   +-- visualizer.html            # Graph traversal visualizer
|   +-- app.js                     # Map Explorer logic (Leaflet, search, routing UI)
|   +-- delivery.js                # Delivery Planner logic
|   +-- style.css                  # Shared styles across all pages
|
+-- tests/
|   +-- test_algorithms.py         # pytest suite - core algorithm tests
|   +-- test_dev_b.py              # Dev B algorithm and route tests
|
+-- requirements.txt
```

---

## Design Decisions

**Why hand-write everything?**
The point of the project was to actually implement the algorithms, not call `nx.dijkstra_path()` or `sklearn.cluster.KMeans()`. Every data structure in `core/` was written from scratch. If a recruiter asks how the routing works, the answer is never "a library does it" - it is the specific algorithm, the complexity, and here is the code.

**Why adjacency list and not a matrix? (Dev A)**
A street corner connects to three or four roads at most, not to all 68,610 nodes. An adjacency matrix would allocate O(V^2) slots - about 2.5 billion entries for this graph, almost all empty. The adjacency list uses O(V + E) and stores only the roads that actually exist. For a sparse city network that is the difference between megabytes and gigabytes.

**Why a custom MinHeap and not heapq? (Dev A)**
Python ships `heapq`. In production you would use it. But the constraint here is raw data structures only. Writing the heap manually is what makes it possible to explain in an interview exactly why push and pop are O(log n) - each operation walks at most one path up or down the tree, and the tree is at most 17 levels deep even for a million items.

**Why A* over plain Dijkstra? (Dev A)**
Dijkstra explores equally in every direction - it fans out like a circle from the start. A* adds a Haversine straight-line distance guess to the goal as a heuristic, so the heap sorts by "cost so far + distance still to go". Places that look closer to the goal bubble up first and the search becomes a narrow beam. The heuristic is admissible (straight-line distance never over-estimates the real road distance), which is the mathematical condition that guarantees A* returns the same optimal path as Dijkstra.

**Why separate the graph from the Trie? (Dev A + Dev B)**
Two completely different problems. The OSM graph is for routing - 68,610 intersection nodes with no human-readable names, identified by integer IDs. The Trie holds 60 named POIs (places like Marina Beach and Chennai Central) for the search box. The user types a name, gets a lat/lon coordinate back from the Trie, and from that point the routing engine takes over.

**Why Redis with in-memory LRU fallback? (Dev A)**
Redis is not guaranteed to be installed on every machine that clones this repo. The fallback means the server starts and works without it - Redis just makes repeated route queries faster. `cache.py` handles both cases transparently behind the same interface.

**Why a 200-node subgraph for the visualizer? (Dev A)**
Running BFS or Dijkstra on 68,610 nodes and streaming every step to the browser would produce tens of thousands of animation frames. 200 nodes gives enough structure to actually watch the algorithm work without overwhelming the browser's memory or the D3 render loop.

**Why Held-Karp and not a greedy TSP? (Dev B)**
Greedy nearest-neighbour is fast at O(n^2) but can produce routes 20-30% longer than optimal depending on the stop layout. Held-Karp is exact - it finds the provably shortest visiting order using bitmask DP. The O(2^n * n^2) cost is acceptable up to 20 stops, and beyond that K-means++ splits the problem first.

**Why K-means++ over standard K-means? (Dev B)**
Standard K-means picks initial centroids randomly, which can converge to poor clusters. K-means++ spreads the initial centroids using a distance-weighted probability distribution - typically 2-5x fewer iterations to convergence and more consistent cluster quality across runs.

---

## Limitations

- Dijkstra on the full 68,610-node graph takes ~2 seconds. A* is faster but still slow on very long cross-city routes - the heuristic helps but the graph is large.
- The Held-Karp cap of 20 stops is a hard algorithmic limit - O(2^n * n^2) becomes infeasible beyond that, not a design choice.
- Traffic data is synthetic - the 168 hourly buckets are randomly seeded, not pulled from real traffic feeds.
- The frontend is three static HTML files served by Python's built-in HTTP server. No build step, no bundler.
- `chennai_graph.json` is not committed to the repo (too large for git). Run `download_osm.py` once after cloning.

---

## Future Work

- Replace synthetic traffic data with real feeds (TomTom / HERE API)
- A* bidirectional search to cut routing time on long cross-city paths
- Persistent Redis deployment so the cache survives server restarts
- WebSocket streaming for the visualizer instead of a single JSON payload
- Expand Trie POIs beyond 60 - the data structure handles it, the data just needs to be added
