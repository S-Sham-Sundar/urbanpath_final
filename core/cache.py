"""
UrbanPath — Cache layer (Dev B · Ajith)

Tries Redis first (5-minute TTL); falls back to an in-process LRU dict
so the server works even without Redis installed.
"""

import json
import time
from typing import Any, Optional

# ── Redis attempt ─────────────────────────────────────────────────────────────

REDIS_AVAILABLE = False
_redis = None

try:
    import redis as _redis_lib
    _redis = _redis_lib.Redis(host="localhost", port=6379, db=0,
                              socket_connect_timeout=1,
                              socket_timeout=1)
    _redis.ping()
    REDIS_AVAILABLE = True
    print("[cache] Redis connected ✓  (5-min TTL)")
except Exception:
    print("[cache] Redis not available — using in-memory fallback cache")

# ── In-memory fallback ────────────────────────────────────────────────────────

_MEM: dict[str, str] = {}
_TTL: dict[str, float] = {}
_MEM_MAX = 1024


def _evict_one():
    if _TTL:
        oldest = min(_TTL, key=_TTL.get)   # type: ignore[arg-type]
        _MEM.pop(oldest, None)
        _TTL.pop(oldest, None)


# ── Public API ────────────────────────────────────────────────────────────────

DEFAULT_TTL = 300   # 5 minutes


def get(key: str) -> Optional[Any]:
    try:
        if REDIS_AVAILABLE:
            raw = _redis.get(key)   # type: ignore[union-attr]
            return json.loads(raw) if raw else None
        raw = _MEM.get(key)
        if raw and time.monotonic() < _TTL.get(key, 0):
            return json.loads(raw)
        _MEM.pop(key, None)
        _TTL.pop(key, None)
        return None
    except Exception:
        return None


def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    try:
        serialised = json.dumps(value, default=str)
        if REDIS_AVAILABLE:
            _redis.setex(key, ttl, serialised)   # type: ignore[union-attr]
        else:
            if len(_MEM) >= _MEM_MAX:
                _evict_one()
            _MEM[key] = serialised
            _TTL[key] = time.monotonic() + ttl
    except Exception:
        pass


def make_key(*parts: Any) -> str:
    return ":".join(str(p) for p in parts)
