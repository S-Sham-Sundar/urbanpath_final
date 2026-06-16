"""
Trie — Location Autocomplete
Developer B: Ajith

O(k) prefix lookup where k = length of the query string.
A linear scan over n locations costs O(n·k) per keystroke — infeasible at
100K+ POIs. The Trie shares common prefixes so we walk directly to the right
subtree in O(k) and collect results from there.
"""


class TrieNode:
    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}
        self.is_end: bool = False       # marks a complete location name
        self.location_data: dict = {}   # stores lat/lon/type at the leaf


class Trie:
    """
    Prefix tree for instant location autocomplete.

    Insert  : O(k)
    Search  : O(k + m)  — k to reach the prefix node, m results collected
    """

    def __init__(self):
        self.root = TrieNode()
        self._size = 0

    # ── INSERT ────────────────────────────────────────────────────────────────

    def insert(self, name: str, data: dict) -> None:
        """
        Walk down the tree one character at a time, creating nodes as needed.
        Store location metadata at the terminal node.
        """
        node = self.root
        for ch in name.lower():
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.location_data = data
        self._size += 1

    # ── SEARCH ────────────────────────────────────────────────────────────────

    def search_prefix(self, prefix: str, limit: int = 10) -> list[dict]:
        """
        Return up to `limit` locations whose names start with `prefix`.
        Step 1: walk to the prefix node  — O(k)
        Step 2: DFS from there collecting all ends — O(m)
        """
        node = self.root
        for ch in prefix.lower():
            if ch not in node.children:
                return []
            node = node.children[ch]

        results: list[dict] = []
        self._dfs_collect(node, prefix.lower(), results, limit)
        return results

    def _dfs_collect(self, node: TrieNode, current: str, results: list, limit: int) -> None:
        if len(results) >= limit:
            return
        if node.is_end:
            results.append({"name": current, **node.location_data})
        for ch, child in node.children.items():
            if len(results) >= limit:
                return
            self._dfs_collect(child, current + ch, results, limit)

    # ── EXACT MATCH ──────────────────────────────────────────────────────────

    def exact_search(self, name: str) -> dict | None:
        """O(k) exact lookup. Returns location data or None."""
        node = self.root
        for ch in name.lower():
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node.location_data if node.is_end else None

    def __len__(self) -> int:
        return self._size

    def __contains__(self, name: str) -> bool:
        return self.exact_search(name) is not None


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    trie = Trie()
    locations = [
        ("Marina Beach",  {"lat": 13.0500, "lon": 80.2824, "type": "beach"}),
        ("Mall Road",     {"lat": 13.0827, "lon": 80.2707, "type": "road"}),
        ("Mandaveli",     {"lat": 13.0209, "lon": 80.2674, "type": "area"}),
        ("Mount Road",    {"lat": 13.0604, "lon": 80.2496, "type": "road"}),
        ("Mylapore",      {"lat": 13.0368, "lon": 80.2676, "type": "area"}),
        ("Anna Nagar",    {"lat": 13.0850, "lon": 80.2101, "type": "area"}),
        ("Adyar",         {"lat": 13.0012, "lon": 80.2565, "type": "area"}),
    ]
    for name, data in locations:
        trie.insert(name, data)

    print("Prefix 'ma':", trie.search_prefix("ma"))
    print("Exact 'Adyar':", trie.exact_search("adyar"))
    print(f"Total locations: {len(trie)}")
