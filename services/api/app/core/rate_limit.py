import hashlib
import hmac
import math
import secrets
import time

from app.core.errors import APIError


class RateLimiter:
    """Ephemeral, bounded counters. Content and raw client addresses are never retained."""

    def __init__(self, per_minute: int, max_keys: int = 10000) -> None:
        self.per_minute = per_minute
        self.max_keys = max_keys
        self.salt = secrets.token_bytes(32)
        self.buckets: dict[bytes, tuple[int, float]] = {}

    def check(self, address: str, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        for key in [key for key, (_, expiry) in self.buckets.items() if expiry <= now]:
            del self.buckets[key]
        key = hmac.digest(self.salt, address.encode(), hashlib.sha256)
        count, expiry = self.buckets.get(key, (0, now + 60))
        if (
            count >= self.per_minute
            or key not in self.buckets
            and len(self.buckets) >= self.max_keys
        ):
            raise APIError(429, "RATE_LIMITED", retry_after=max(1, math.ceil(expiry - now)))
        self.buckets[key] = (count + 1, expiry)
