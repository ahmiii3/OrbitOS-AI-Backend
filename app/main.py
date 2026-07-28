from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import check_db_connection, init_db
from app.core.exceptions import setup_exception_handlers
from app.core.redis import close_redis_pool, get_redis
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle events (startup and shutdown)."""
    # Startup: can initialize connection pools or verify connections
    yield
    # Shutdown: gracefully close Redis connection pool
    await close_redis_pool()


def create_app() -> FastAPI:
    """Factory function to initialize and configure the FastAPI application."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="Production-ready enterprise SaaS authentication and user management API.",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure Rate Limiting Middleware
    application.add_middleware(
        RateLimitMiddleware,
        requests_limit=60,
        window_seconds=60,
    )

    # Register Domain Exception Handlers
    setup_exception_handlers(application)

    # Include API Routers
    application.include_router(api_router, prefix=settings.API_V1_STR)

    # Register Tortoise ORM
    init_db(application)

    @application.get(
        "/health",
        status_code=status.HTTP_200_OK,
        tags=["System"],
        summary="Health check endpoint",
        description="Verifies the operational status of the API, PostgreSQL database, and Redis cache.",
    )
    async def health_check() -> Dict[str, str]:
        db_status = "ok" if await check_db_connection() else "unreachable"
        redis_status = "ok"

        # Check Redis
        try:
            redis_client = await get_redis()
            await redis_client.ping()
            await redis_client.aclose()
        except Exception as exc:
            redis_status = f"unreachable: {exc}"

        overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
        return {
            "status": overall,
            "database": db_status,
            "redis": redis_status,
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
        }

    return application


app = create_app()
