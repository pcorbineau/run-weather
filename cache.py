import hashlib
import json
from datetime import date, datetime
from diskcache import Cache as DCache

from config import CACHE_DIR, CACHE_TTL_DAYS


class WeatherCache:
    def __init__(self):
        self._cache = DCache(str(CACHE_DIR))

    def _make_key(self, dt: date, lat: float, lon: float) -> str:
        key = f"{dt.isoformat()},{lat:.2f},{lon:.2f}"
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, dt: date, lat: float, lon: float) -> list[dict] | None:
        key = self._make_key(dt, lat, lon)
        val = self._cache.get(key)
        if val is None:
            return None
        return val

    def set(self, dt: date, lat: float, lon: float, data: list[dict]) -> None:
        key = self._make_key(dt, lat, lon)
        self._cache.set(key, data, expire=CACHE_TTL_DAYS * 86400)

    def close(self) -> None:
        self._cache.close()
