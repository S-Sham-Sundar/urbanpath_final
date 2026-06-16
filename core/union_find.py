"""
Union-Find (Disjoint Set Union) — Connectivity + Kruskal's MST
Developer B: Ajith

Answers "is there any path between node A and node B?" in near-constant time.
Without DSU, you'd need BFS/DFS — O(V + E) per query.
With path compression + union by rank: O(α(n)) ≈ O(1) amortized.

α(n) is the inverse Ackermann function — grows so slowly it's effectively
constant for any real-world n.
"""


class UnionFind:
    """
    Disjoint Set Union with:
    - Path compression  : flattens the tree on every find()
    - Union by rank     : always attach the smaller tree under the larger
    """

    def __init__(self, n: int):
        """
        Initialise n singleton sets {0}, {1}, ..., {n-1}.
        parent[i] = i means i is its own root.
        rank[i] tracks the upper bound on tree height.
        """
        self.parent: list[int] = list(range(n))
        self.rank: list[int] = [0] * n
        self.num_components: int = n

    # ── FIND ──────────────────────────────────────────────────────────────────

    def find(self, x: int) -> int:
        """
        Return the representative (root) of x's set.
        Path compression: every node on the path is wired directly to the root,
        so future queries on these nodes cost O(1).
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])   # path compression
        return self.parent[x]

    # ── UNION ─────────────────────────────────────────────────────────────────

    def union(self, x: int, y: int) -> bool:
        """
        Merge the sets containing x and y.
        Returns True if they were in different sets (a new edge in the MST).
        Returns False if already connected (would create a cycle).
        Union by rank: attach smaller-rank tree under higher-rank root.
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False                        # already in the same set

        # attach lower rank under higher rank
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

        self.num_components -= 1
        return True

    # ── QUERIES ───────────────────────────────────────────────────────────────

    def connected(self, x: int, y: int) -> bool:
        """True if x and y are in the same component."""
        return self.find(x) == self.find(y)

    def component_count(self) -> int:
        """Number of disjoint components currently in the structure."""
        return self.num_components


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uf = UnionFind(6)
    edges = [(0, 1), (1, 2), (3, 4)]
    for u, v in edges:
        uf.union(u, v)

    print("0-2 connected:", uf.connected(0, 2))   # True  (0-1-2)
    print("0-3 connected:", uf.connected(0, 3))   # False
    print("Components:", uf.component_count())    # 3
