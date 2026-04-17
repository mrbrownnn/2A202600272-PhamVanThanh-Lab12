"""Redis-backed rate limiter for stateless API instances."""

import time
from collections import defaultdict, deque

import redis
from fastapi import HTTPException

from app.config import settings


class RateLimiter:
    def __init__(self, redis_url: str, max_requests_per_minute: int):
        self.max_requests_per_minute = max_requests_per_minute
        self.redis_client = None
        self._windows: dict[str, deque] = defaultdict(deque)

        if redis_url:
            try:
                self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except redis.RedisError:
                self.redis_client = None

    def check(self, bucket_key: str):
        if self.redis_client:
            self._check_redis(bucket_key)
        else:
            self._check_memory(bucket_key)

    def _check_redis(self, bucket_key: str):
        key = f"rate:{bucket_key}:{int(time.time() // 60)}"
        try:
            count = self.redis_client.incr(key)
            if count == 1:
                self.redis_client.expire(key, 65)
        except redis.RedisError as exc:
            raise HTTPException(status_code=503, detail="Rate limiter unavailable") from exc

        if count > self.max_requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.max_requests_per_minute} req/min",
                headers={"Retry-After": "60"},
            )

    def _check_memory(self, bucket_key: str):
        now = time.time()
        window = self._windows[bucket_key]
        while window and window[0] < now - 60:
            window.popleft()

        if len(window) >= self.max_requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.max_requests_per_minute} req/min",
                headers={"Retry-After": "60"},
            )
        window.append(now)
