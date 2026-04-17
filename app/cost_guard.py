"""Cost guard to protect monthly token spend budget."""

import time

import redis
from fastapi import HTTPException


class CostGuard:
    def __init__(self, redis_url: str, monthly_budget_usd: float):
        self.monthly_budget_usd = monthly_budget_usd
        self.redis_client = None
        self._monthly_cost = 0.0
        self._month_key = time.strftime("%Y-%m")

        if redis_url:
            try:
                self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except redis.RedisError:
                self.redis_client = None

    @staticmethod
    def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
        in_cost = (input_tokens / 1000) * 0.00015
        out_cost = (output_tokens / 1000) * 0.00060
        return in_cost + out_cost

    def add_and_check(self, input_tokens: int = 0, output_tokens: int = 0) -> float:
        incremental = self.estimate_cost_usd(input_tokens, output_tokens)

        if self.redis_client:
            return self._add_and_check_redis(incremental)
        return self._add_and_check_memory(incremental)

    def _add_and_check_redis(self, incremental: float) -> float:
        month = time.strftime("%Y-%m")
        key = f"budget:{month}"

        try:
            total = self.redis_client.incrbyfloat(key, incremental)
            if total > self.monthly_budget_usd:
                raise HTTPException(503, "Monthly budget exhausted.")
            return float(total)
        except redis.RedisError as exc:
            raise HTTPException(status_code=503, detail="Cost guard unavailable") from exc

    def _add_and_check_memory(self, incremental: float) -> float:
        month = time.strftime("%Y-%m")
        if month != self._month_key:
            self._month_key = month
            self._monthly_cost = 0.0

        next_total = self._monthly_cost + incremental
        if next_total > self.monthly_budget_usd:
            raise HTTPException(503, "Monthly budget exhausted.")

        self._monthly_cost = next_total
        return self._monthly_cost
