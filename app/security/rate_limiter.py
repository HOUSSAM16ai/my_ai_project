# app/security/rate_limiter.py
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status

class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.history = defaultdict(list)

    async def __call__(self, request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()

        self.history[ip] = [t for t in self.history[ip] if now - t < 60]

        if len(self.history[ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
            )

        self.history[ip].append(now)

rate_limiter = RateLimiter(requests_per_minute=20)
