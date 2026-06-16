"""
UrbanPath — Graph core (Dev A · Sham)
Supports both real OSM data and synthetic fallback.
"""

import math
import json
import os
from typing import Dict, List, Optional, Tuple


# ── Haversine ────────────────────────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km (Haversine formula)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ── Node ─────────────────────────────────────────────────────────────────────

class Node:
    __slots__ = ("id", "lat", "lon", "name")

    def __init__(self, id: str, lat: float, lon: float, name: str = ""):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.name = name or f"Node {id}"

    def __repr__(self):
        return f"Node({self.id}, {self.lat:.5f}, {self.lon:.5f})"


# ── Edge ─────────────────────────────────────────────────────────────────────

class Edge:
    __slots__ = ("from_id", "to_id", "weight", "name")

    def __init__(self, from_id: str, to_id: str, weight: float, name: str = ""):
        self.from_id = from_id
        self.to_id = to_id
        self.weight = weight   # km
        self.name = name

    def __repr__(self):
        return f"Edge({self.from_id}→{self.to_id}, {self.weight:.4f} km)"


# ── Graph ─────────────────────────────────────────────────────────────────────

class Graph:
    """Adjacency-list directed graph with integer-index access for algorithms."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.adj: Dict[str, List[Tuple[str, float]]] = {}
        self._node_list: List[str] = []   # ordered → integer indexing

    # ── Mutation ──────────────────────────────────────────────────────────────

    def add_node(self, node: Node):
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self.adj[node.id] = []
            self._node_list.append(node.id)

    def add_edge(self, edge: Edge):
        if edge.from_id not in self.adj:
            self.adj[edge.from_id] = []
        self.adj[edge.from_id].append((edge.to_id, edge.weight))

    # ── Integer-index access (for Dijkstra / A* / BFS) ───────────────────────

    def get_node_by_index(self, idx: int) -> Optional[Node]:
        if 0 <= idx < len(self._node_list):
            return self.nodes.get(self._node_list[idx])
        return None

    def index_of(self, node_id: str) -> int:
        try:
            return self._node_list.index(node_id)
        except ValueError:
            return -1

    def neighbors_by_index(self, idx: int) -> List[Tuple[int, float]]:
        """Return neighbors as (neighbor_index, weight) pairs."""
        node_id = self._node_list[idx] if 0 <= idx < len(self._node_list) else None
        if node_id is None:
            return []
        result = []
        for nbr_id, w in self.adj.get(node_id, []):
            nbr_idx = self.index_of(nbr_id)
            if nbr_idx >= 0:
                result.append((nbr_idx, w))
        return result

    # ── Metrics ───────────────────────────────────────────────────────────────

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return sum(len(v) for v in self.adj.values())

    def all_edges(self) -> List[Tuple[str, str, float]]:
        return [
            (from_id, to_id, w)
            for from_id, nbrs in self.adj.items()
            for to_id, w in nbrs
        ]

    # ── Serialisation (for /graph API and D3 visualiser) ─────────────────────

    def to_dict(self, max_nodes: int = 300) -> dict:
        """Return a bounded subgraph suitable for the D3 frontend."""
        node_ids = self._node_list[:max_nodes]
        node_set = set(node_ids)
        nodes_out = []
        for nid in node_ids:
            n = self.nodes[nid]
            nodes_out.append({
                "id": nid,
                "index": self.index_of(nid),
                "lat": n.lat,
                "lon": n.lon,
                "name": n.name,
            })
        edges_out = []
        for nid in node_ids:
            for nbr_id, w in self.adj.get(nid, []):
                if nbr_id in node_set:
                    edges_out.append({
                        "from": nid,
                        "to": nbr_id,
                        "weight": round(w, 4),
                    })
        return {
            "total_nodes": self.node_count(),
            "total_edges": self.edge_count(),
            "shown_nodes": len(nodes_out),
            "nodes": nodes_out,
            "edges": edges_out,
        }
