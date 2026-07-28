from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from tortoise import Tortoise
from app.core.config import settings


def init_db(app: FastAPI) -> None:
    """Register Tortoise ORM with the FastAPI application lifecycle."""
    register_tortoise(
        app,
        config=settings.TORTOISE_ORM,
        generate_schemas=False,  # Schemas managed via Aerich migrations
        add_exception_handlers=True,
    )


async def check_db_connection() -> bool:
    """Verify live connectivity to PostgreSQL / Supabase via Tortoise connection pool."""
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        return True
    except Exception:
        return False
