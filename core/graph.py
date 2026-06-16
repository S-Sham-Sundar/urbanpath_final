"""
Graph Representation — Adjacency List + Edge Weights
Developer A: Sham

City road network modelled as G = (V, E) where:
  V = intersections, each with (lat, lon) coordinates
  E = road segments weighted by distance × traffic factor

Adjacency list chosen over matrix:
  - Matrix costs O(V²) space — wasteful for sparse city graphs
  - List costs O(V + E) space — city graphs are sparse (avg degree ~3-4)
"""

import math


class Node:
    """An intersection in the road network."""
    def __init__(self, node_id: int, lat: float, lon: float, name: str = ""):
        self.id = node_id
        self.lat = lat
        self.lon = lon
        self.name = name

    def __repr__(self):
        return f"Node({self.id}, {self.name or f'{self.lat:.4f},{self.lon:.4f}'})"


class Edge:
    """A directed road segment between two intersections."""
    def __init__(self, src: int, dst: int, weight: float, road_name: str = ""):
        self.src = src
        self.dst = dst
        self.weight = weight        # distance in km × traffic factor
        self.road_name = road_name

    def __repr__(self):
        return f"Edge({self.src}→{self.dst}, w={self.weight:.2f})"


class Graph:
    """
    Directed weighted graph using adjacency list representation.
    Supports both directed and undirected (bidirectional) edges.
    """

    def __init__(self):
        self.nodes: dict[int, Node] = {}
        self.adj: dict[int, list[Edge]] = {}    # adjacency list
        self._edge_count = 0

    # ── BUILD ─────────────────────────────────────────────────────────────────

    def add_node(self, node_id: int, lat: float, lon: float, name: str = "") -> None:
        self.nodes[node_id] = Node(node_id, lat, lon, name)
        if node_id not in self.adj:
            self.adj[node_id] = []

    def add_edge(self, src: int, dst: int, weight: float,
                 bidirectional: bool = True, road_name: str = "") -> None:
        """Add a weighted edge. Bidirectional by default (most roads)."""
        self.adj[src].append(Edge(src, dst, weight, road_name))
        self._edge_count += 1
        if bidirectional:
            self.adj[dst].append(Edge(dst, src, weight, road_name))
            self._edge_count += 1

    # ── QUERIES ───────────────────────────────────────────────────────────────

    def neighbors(self, node_id: int) -> list[Edge]:
        return self.adj.get(node_id, [])

    def haversine(self, u: int, v: int) -> float:
        """
        Great-circle distance between two nodes in km.
        Used as the admissible heuristic in A*.
        """
        R = 6371.0  # Earth radius in km
        lat1, lon1 = math.radians(self.nodes[u].lat), math.radians(self.nodes[u].lon)
        lat2, lon2 = math.radians(self.nodes[v].lat), math.radians(self.nodes[v].lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    def all_edges(self) -> list[tuple]:
        """Return all edges as (weight, src, dst) — used by Kruskal."""
        seen = set()
        result = []
        for src, edges in self.adj.items():
            for e in edges:
                key = (min(src, e.dst), max(src, e.dst))
                if key not in seen:
                    seen.add(key)
                    result.append((e.weight, src, e.dst))
        return result

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return self._edge_count

    def __repr__(self):
        return f"Graph(V={self.num_nodes}, E={self.num_edges})"


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    g = Graph()
    g.add_node(0, 13.0827, 80.2707, "Central Station")
    g.add_node(1, 13.0500, 80.2824, "Marina Beach")
    g.add_node(2, 13.0368, 80.2676, "Mylapore")
    g.add_node(3, 13.0012, 80.2565, "Adyar")

    g.add_edge(0, 1, 4.2, road_name="Anna Salai")
    g.add_edge(1, 2, 2.1, road_name="Kamaraj Salai")
    g.add_edge(2, 3, 3.8, road_name="TTK Road")
    g.add_edge(0, 2, 5.5, road_name="Inner Ring Road")

    print(g)
    print("Neighbors of node 0:", g.neighbors(0))
    print("Haversine 0→3:", round(g.haversine(0, 3), 3), "km")
