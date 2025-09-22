import asyncio, json, time
from typing import Any, Optional
try:
    import redis  # type: ignore
except Exception:
    redis = None

class InMemoryTTL:
    def __init__(self, ttl=120):
        self.ttl = ttl
        self.store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        row = self.store.get(key)
        if not row: return None
        exp, value = row
        if time.time() > exp:
            self.store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self.store[key] = (time.time() + (ttl or self.ttl), value)

class Cache:
    def __init__(self, redis_url: str | None = None, default_ttl: int = 120):
        self.default_ttl = default_ttl
        self.local = InMemoryTTL(default_ttl)
        self.r: Optional["redis.Redis"] = None
        if redis_url and redis:
            try:
                self.r = redis.from_url(redis_url, decode_responses=True)
            except Exception:
                self.r = None

    async def aget(self, key: str) -> Optional[Any]:
        if self.r:
            val = await asyncio.to_thread(self.r.get, key)
            return json.loads(val) if val else None
        return self.local.get(key)

    async def aset(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or self.default_ttl
        if self.r:
            s = json.dumps(value)
            await asyncio.to_thread(self.r.setex, key, ttl, s)
        else:
            self.local.set(key, value, ttl)
