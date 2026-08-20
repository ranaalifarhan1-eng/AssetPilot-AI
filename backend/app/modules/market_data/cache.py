import time
import asyncio
from typing import Dict, Any, Optional

class MarketDataCache:
    def __init__(self, ticker_ttl: float = 10.0, candle_ttl: float = 30.0):
        self._ticker_ttl = ticker_ttl
        self._candle_ttl = candle_ttl
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if time.time() > entry["expires_at"]:
                del self._store[key]
                return None
            return entry["data"]

    async def set(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        if ttl is None:
            ttl = self._ticker_ttl
        expires_at = time.time() + ttl
        async with self._lock:
            self._store[key] = {
                "data": data,
                "expires_at": expires_at
            }

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

global_cache = MarketDataCache()
