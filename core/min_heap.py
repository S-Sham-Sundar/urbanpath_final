"""
Custom Min-Heap — Priority Queue
Developer A: Sham

Powers Dijkstra, A*, and the delivery scheduler.
Built from scratch — no heapq import.

Why a custom heap?
  heapq works fine, but implementing it demonstrates understanding of the
  underlying structure. Dijkstra without a heap degrades from O(E log V)
  to O(V²) — the heap is what keeps routing fast on large city graphs.

Operations:
  push   : O(log n) — add element, sift up
  pop    : O(log n) — remove minimum, sift down
  peek   : O(1)
"""


class MinHeap:
    """
    Binary min-heap storing (priority, data) tuples.
    The element with the smallest priority is always at index 0.
    """

    def __init__(self):
        self._heap: list[tuple] = []

    # ── CORE OPERATIONS ───────────────────────────────────────────────────────

    def push(self, priority: float, data) -> None:
        """Insert (priority, data) and restore heap property via sift-up."""
        self._heap.append((priority, data))
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> tuple:
        """
        Remove and return the minimum element.
        Swap root with last, shrink heap, then sift-down to restore order.
        """
        if not self._heap:
            raise IndexError("pop from empty heap")
        if len(self._heap) == 1:
            return self._heap.pop()

        min_item = self._heap[0]
        self._heap[0] = self._heap.pop()   # move last to root
        self._sift_down(0)
        return min_item

    def peek(self) -> tuple:
        if not self._heap:
            raise IndexError("peek at empty heap")
        return self._heap[0]

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    # ── SIFT OPERATIONS ───────────────────────────────────────────────────────

    def _sift_up(self, idx: int) -> None:
        """
        Bubble element at idx upward until heap property is satisfied.
        parent of idx is at (idx - 1) // 2.
        """
        while idx > 0:
            parent = (idx - 1) // 2
            if self._heap[idx][0] < self._heap[parent][0]:
                self._heap[idx], self._heap[parent] = self._heap[parent], self._heap[idx]
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        """
        Push element at idx downward until heap property is satisfied.
        Children of idx are at 2*idx+1 (left) and 2*idx+2 (right).
        """
        n = len(self._heap)
        while True:
            smallest = idx
            left  = 2 * idx + 1
            right = 2 * idx + 2

            if left < n and self._heap[left][0] < self._heap[smallest][0]:
                smallest = left
            if right < n and self._heap[right][0] < self._heap[smallest][0]:
                smallest = right

            if smallest == idx:
                break
            self._heap[idx], self._heap[smallest] = self._heap[smallest], self._heap[idx]
            idx = smallest


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    h = MinHeap()
    for priority, node in [(5, "E"), (1, "A"), (3, "C"), (2, "B"), (4, "D")]:
        h.push(priority, node)

    print("Popping in order:")
    while h:
        p, node = h.pop()
        print(f"  priority={p}, node={node}")
