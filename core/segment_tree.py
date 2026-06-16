"""
Segment Tree — Traffic Time-Series Queries
Developer B: Ajith

Each road stores 168 hourly traffic readings (7 days × 24 hours).
We need to answer range queries like:
  "What is the minimum traffic weight on road R between hours 8 and 18?"

Naive scan: O(n) per query.
Segment tree: O(log n) build once, O(log n) per query — crucial when
routing has to check traffic across thousands of edges.

This implementation stores range-minimum values (useful for finding
the least-congested time window). Range-sum is also supported.
"""


class SegmentTree:
    """
    Segment tree supporting:
      - Point update  : O(log n)
      - Range minimum : O(log n)
      - Range sum     : O(log n)
    """

    def __init__(self, data: list[float]):
        """
        Build the tree from a flat list of traffic readings.
        Internal array is 4× the input length to guarantee enough space.
        """
        self.n = len(data)
        self.min_tree: list[float] = [float("inf")] * (4 * self.n)
        self.sum_tree: list[float] = [0.0] * (4 * self.n)
        if self.n > 0:
            self._build(data, 0, 0, self.n - 1)

    # ── BUILD ─────────────────────────────────────────────────────────────────

    def _build(self, data: list[float], node: int, start: int, end: int) -> None:
        if start == end:
            self.min_tree[node] = data[start]
            self.sum_tree[node] = data[start]
            return
        mid = (start + end) // 2
        left, right = 2 * node + 1, 2 * node + 2
        self._build(data, left,  start, mid)
        self._build(data, right, mid + 1, end)
        self.min_tree[node] = min(self.min_tree[left], self.min_tree[right])
        self.sum_tree[node] = self.sum_tree[left] + self.sum_tree[right]

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def update(self, idx: int, value: float) -> None:
        """Update a single reading at position idx."""
        self._update(0, 0, self.n - 1, idx, value)

    def _update(self, node: int, start: int, end: int, idx: int, value: float) -> None:
        if start == end:
            self.min_tree[node] = value
            self.sum_tree[node] = value
            return
        mid = (start + end) // 2
        left, right = 2 * node + 1, 2 * node + 2
        if idx <= mid:
            self._update(left,  start, mid,     idx, value)
        else:
            self._update(right, mid + 1, end,   idx, value)
        self.min_tree[node] = min(self.min_tree[left], self.min_tree[right])
        self.sum_tree[node] = self.sum_tree[left] + self.sum_tree[right]

    # ── RANGE QUERIES ─────────────────────────────────────────────────────────

    def range_min(self, l: int, r: int) -> float:
        """Minimum traffic value in the hour window [l, r] inclusive."""
        return self._range_min(0, 0, self.n - 1, l, r)

    def _range_min(self, node: int, start: int, end: int, l: int, r: int) -> float:
        if r < start or end < l:
            return float("inf")         # out of range
        if l <= start and end <= r:
            return self.min_tree[node]  # fully covered
        mid = (start + end) // 2
        left_min  = self._range_min(2 * node + 1, start, mid,     l, r)
        right_min = self._range_min(2 * node + 2, mid + 1, end,   l, r)
        return min(left_min, right_min)

    def range_sum(self, l: int, r: int) -> float:
        """Sum of traffic values in the hour window [l, r] inclusive."""
        return self._range_sum(0, 0, self.n - 1, l, r)

    def _range_sum(self, node: int, start: int, end: int, l: int, r: int) -> float:
        if r < start or end < l:
            return 0.0
        if l <= start and end <= r:
            return self.sum_tree[node]
        mid = (start + end) // 2
        return (
            self._range_sum(2 * node + 1, start, mid,   l, r) +
            self._range_sum(2 * node + 2, mid + 1, end, l, r)
        )

    # ── TRAFFIC HELPER ────────────────────────────────────────────────────────

    def best_travel_hour(self, start_hour: int, end_hour: int) -> int:
        """
        Return the hour index with minimum traffic in the given window.
        Used by the traffic-aware router to pick the best departure time.
        """
        best_val = float("inf")
        best_hour = start_hour
        for h in range(start_hour, end_hour + 1):
            val = self.range_min(h, h)
            if val < best_val:
                best_val = val
                best_hour = h
        return best_hour


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Simulate 24 hours of traffic on one road (Mon 00:00 – 23:00)
    hourly_traffic = [
        0.3, 0.2, 0.2, 0.2, 0.3, 0.5,   # 00–05 (night, quiet)
        0.8, 1.5, 1.9, 1.7, 1.3, 1.1,   # 06–11 (morning rush)
        1.0, 0.9, 0.8, 0.9, 1.1, 1.8,   # 12–17 (midday + build)
        2.0, 1.6, 1.2, 0.9, 0.6, 0.4,   # 18–23 (evening rush + taper)
    ]
    st = SegmentTree(hourly_traffic)

    print("Min traffic 08–18:", st.range_min(8, 18))     # peak window
    print("Best hour 06–10:", st.best_travel_hour(6, 10))
    print("Total traffic 00–23:", st.range_sum(0, 23))

    # Update hour 9 (update a reading)
    st.update(9, 0.5)
    print("After update — min 08–18:", st.range_min(8, 18))
