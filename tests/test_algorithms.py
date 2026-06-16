"""
Unit Tests — UrbanPath Core Algorithms
Tests both Developer A and Developer B implementations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import math
import pytest

# ── Dev B ─────────────────────────────────────────────────────────────────────

def test_trie_insert_and_search():
    from core.trie import Trie
    t = Trie()
    t.insert("Marina Beach", {"lat": 13.05, "lon": 80.28, "type": "beach"})
    t.insert("Mylapore",     {"lat": 13.03, "lon": 80.26, "type": "area"})
    t.insert("Mount Road",   {"lat": 13.06, "lon": 80.24, "type": "road"})

    results = t.search_prefix("m")
    assert len(results) == 3

    results = t.search_prefix("my")
    assert any("mylapore" in r["name"] for r in results)

    assert t.exact_search("marina beach") is not None
    assert t.exact_search("adyar") is None
    assert len(t) == 3


def test_trie_empty_prefix():
    from core.trie import Trie
    t = Trie()
    assert t.search_prefix("xyz") == []


def test_union_find_basic():
    from core.union_find import UnionFind
    uf = UnionFind(5)
    assert not uf.connected(0, 4)
    uf.union(0, 1)
    uf.union(1, 2)
    assert uf.connected(0, 2)
    assert not uf.connected(0, 3)
    assert uf.component_count() == 3


def test_union_find_path_compression():
    from core.union_find import UnionFind
    uf = UnionFind(10)
    for i in range(9):
        uf.union(i, i + 1)
    assert uf.connected(0, 9)
    assert uf.component_count() == 1


def test_kruskal_mst():
    from core.kruskal import kruskal_mst
    edges = [(2, 0, 1), (3, 0, 3), (6, 1, 2), (8, 1, 4), (5, 2, 4), (7, 3, 4)]
    mst, cost = kruskal_mst(5, edges)
    assert len(mst) == 4                    # V - 1 edges
    assert cost == pytest.approx(16.0)      # 2 + 3 + 5 + 6


def test_segment_tree_range_min():
    from core.segment_tree import SegmentTree
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    st = SegmentTree(data)
    assert st.range_min(0, 7) == 1
    assert st.range_min(4, 7) == 2
    assert st.range_min(2, 4) == 1


def test_segment_tree_update():
    from core.segment_tree import SegmentTree
    data = [5, 3, 7, 2, 8]
    st = SegmentTree(data)
    assert st.range_min(0, 4) == 2
    st.update(3, 10)
    assert st.range_min(0, 4) == 3


def test_held_karp_small():
    from core.tsp_held_karp import held_karp
    dist = [
        [0, 1, 2, 3],
        [1, 0, 1, 2],
        [2, 1, 0, 1],
        [3, 2, 1, 0],
    ]
    cost, path = held_karp(dist)
    assert cost == pytest.approx(6.0)   # 0→1→2→3→0 = 1+1+1+3 = 6? no: 0→1→2→3→0
    assert path[0] == 0
    assert path[-1] == 0


def test_kmeans_clustering():
    from core.kmeans import kmeans_cluster, recommend_k
    points = [(float(i), float(i % 5)) for i in range(30)]
    k = recommend_k(30, max_cluster_size=15)
    clusters = kmeans_cluster(points, k)
    total = sum(len(c) for c in clusters)
    assert total == 30


# ── Dev A ─────────────────────────────────────────────────────────────────────

def _build_test_graph():
    from core.graph import Graph
    g = Graph()
    for nid, lat, lon, name in [
        (0, 13.08, 80.27, "A"),
        (1, 13.05, 80.28, "B"),
        (2, 13.03, 80.26, "C"),
        (3, 13.00, 80.25, "D"),
    ]:
        g.add_node(nid, lat, lon, name)
    g.add_edge(0, 1, 4.0)
    g.add_edge(1, 2, 2.0)
    g.add_edge(2, 3, 3.0)
    g.add_edge(0, 3, 12.0)
    return g


def test_min_heap_order():
    from core.min_heap import MinHeap
    h = MinHeap()
    for p, v in [(5, "e"), (1, "a"), (3, "c"), (2, "b"), (4, "d")]:
        h.push(p, v)
    pops = [h.pop()[0] for _ in range(5)]
    assert pops == sorted(pops)


def test_dijkstra_shortest_path():
    from core.dijkstra import dijkstra
    g = _build_test_graph()
    dist, path = dijkstra(g, 0, 3)
    assert dist == pytest.approx(9.0)   # 0→1→2→3 = 4+2+3
    assert path == [0, 1, 2, 3]


def test_astar_matches_dijkstra():
    from core.astar import astar
    from core.dijkstra import dijkstra
    g = _build_test_graph()
    d_dist, _ = dijkstra(g, 0, 3)
    a_dist, _ = astar(g, 0, 3)
    assert d_dist == pytest.approx(a_dist)


def test_bfs_isochrone():
    from core.bfs_isochrone import bfs_isochrone
    g = _build_test_graph()
    reachable = bfs_isochrone(g, src=0, time_limit=6.5)
    assert 0 in reachable
    assert 1 in reachable   # distance 4.0
    assert 2 in reachable   # distance 6.0
    assert 3 not in reachable  # distance 9.0 > 6.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
