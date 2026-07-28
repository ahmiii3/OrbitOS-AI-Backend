import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis import get_redis_pool
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis sliding window counter placeholder."""

    def __init__(self, app: Callable, requests_limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Rate limit only sensitive authentication endpoints
        path = request.url.path
        if not any(path.endswith(endpoint) for endpoint in ["/login", "/register", "/forgot-password", "/reset-password"]):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        rate_key = f"rate_limit:{client_ip}:{path}"

        try:
            pool = get_redis_pool()
            redis = Redis(connection_pool=pool)
            current_count = await redis.incr(rate_key)
            if current_count == 1:
                await redis.expire(rate_key, self.window_seconds)
            await redis.aclose()

            if current_count > self.requests_limit:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on {path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "RateLimitExceededError",
                        "message": "Too many requests. Please try again later.",
                        "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )
        except Exception as exc:
            # If Redis connection fails in middleware, log warning and allow request to proceed fail-open
            logger.debug(f"Rate limiting check bypassed due to Redis error: {exc}")

        return await call_next(request)
