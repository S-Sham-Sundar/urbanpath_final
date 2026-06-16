"""
K-means++ Clustering — Scale Delivery to 100+ Stops
Developer B: Ajith

Held-Karp is exact but exponential — O(2ⁿ · n²). At n=20 that's fine.
At n=100 it's astronomically slow (2¹⁰⁰ states).

Cluster-first strategy:
  1. Split 100+ stops into k clusters using K-means++
  2. Run Held-Karp on each cluster (each cluster ≤ 20 stops)
  3. Stitch the cluster tours together

Why K-means++ over standard K-means?
  Standard K-means picks centroids randomly → can converge to bad clusters.
  K-means++ spreads initial centroids apart using a distance-weighted
  probability distribution → consistently better cluster quality,
  typically 2–5× fewer iterations to convergence.

Time: O(k · n · iters)  where iters is usually 10–30
"""

import math
import random


def _euclidean(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _nearest_centroid_dist(point: tuple, centroids: list[tuple]) -> float:
    """Distance from a point to its nearest centroid."""
    return min(_euclidean(point, c) for c in centroids)


# ── K-MEANS++ INIT ───────────────────────────────────────────────────────────

def _kmeanspp_init(points: list[tuple], k: int, rng: random.Random) -> list[tuple]:
    """
    K-means++ initialisation:
    - Pick first centroid uniformly at random
    - Each subsequent centroid is chosen with probability ∝ D(x)²
      where D(x) = distance to nearest already-chosen centroid
    This spreads centroids apart, avoiding bad random starts.
    """
    centroids = [rng.choice(points)]
    for _ in range(k - 1):
        weights = [_nearest_centroid_dist(p, centroids) ** 2 for p in points]
        total = sum(weights)
        r = rng.random() * total
        cumulative = 0.0
        for point, w in zip(points, weights):
            cumulative += w
            if cumulative >= r:
                centroids.append(point)
                break
        else:
            centroids.append(points[-1])
    return centroids


# ── K-MEANS ──────────────────────────────────────────────────────────────────

def kmeans_cluster(
    points: list[tuple[float, float]],
    k: int,
    max_iters: int = 100,
    seed: int = 42,
) -> list[list[int]]:
    """
    Cluster `points` into k groups using K-means++.

    Parameters
    ----------
    points    : list of (lat, lon) coordinates
    k         : number of clusters (set k so each cluster ≤ 20 stops)
    max_iters : iteration cap (converges well before this in practice)
    seed      : random seed for reproducibility

    Returns
    -------
    clusters : list of k lists, each containing the indices of points in that cluster
    """
    if len(points) <= k:
        return [[i] for i in range(len(points))]

    rng = random.Random(seed)
    centroids = _kmeanspp_init(points, k, rng)

    assignments = [0] * len(points)

    for _ in range(max_iters):
        # Assignment step: assign each point to the nearest centroid
        changed = False
        for i, p in enumerate(points):
            nearest = min(range(k), key=lambda c: _euclidean(p, centroids[c]))
            if nearest != assignments[i]:
                assignments[i] = nearest
                changed = True

        if not changed:
            break

        # Update step: move each centroid to the mean of its assigned points
        new_centroids = []
        for c in range(k):
            members = [points[i] for i, a in enumerate(assignments) if a == c]
            if members:
                lat_mean = sum(p[0] for p in members) / len(members)
                lon_mean = sum(p[1] for p in members) / len(members)
                new_centroids.append((lat_mean, lon_mean))
            else:
                new_centroids.append(centroids[c])   # keep old if empty
        centroids = new_centroids

    # Group indices by cluster
    clusters: list[list[int]] = [[] for _ in range(k)]
    for i, a in enumerate(assignments):
        clusters[a].append(i)

    return [c for c in clusters if c]   # drop empty clusters


def recommend_k(num_stops: int, max_cluster_size: int = 15) -> int:
    """Suggest k so no cluster exceeds max_cluster_size stops."""
    return math.ceil(num_stops / max_cluster_size)


# ── DEMO ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import random as _r
    _r.seed(0)
    # Simulate 40 random delivery stops in Chennai bounding box
    stops = [(13.0 + _r.random() * 0.15, 80.2 + _r.random() * 0.15) for _ in range(40)]
    k = recommend_k(len(stops))
    clusters = kmeans_cluster(stops, k)
    print(f"40 stops → {k} clusters")
    for idx, cl in enumerate(clusters):
        print(f"  Cluster {idx}: {len(cl)} stops")
