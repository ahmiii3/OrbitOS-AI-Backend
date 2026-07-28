import asyncio
from tortoise import Tortoise
from app.core.config import TORTOISE_ORM_CONFIG

async def main():
    print("Initializing Tortoise...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    print("Generating schemas...")
    # generate_schemas(safe=True) will create tables if they don't exist
    await Tortoise.generate_schemas(safe=True)
    print("Schemas generated successfully.")
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
