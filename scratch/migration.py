import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    # Use DATABASE_URI_OVERRIDE if present, otherwise default to localhost
    override = os.getenv("DATABASE_URI_OVERRIDE")
    ssl_context = False
    if override:
        db_uri = override.replace("+asyncpg", "")
        if "?ssl=require" in db_uri:
            db_uri = db_uri.replace("?ssl=require", "")
            ssl_context = True # or 'require' depending on asyncpg version, True usually works
    else:
        db_uri = "postgresql://postgres:password@localhost:5432/saas_auth_db"
        
    print(f"Connecting to {db_uri}...")
    try:
        if ssl_context:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = await asyncpg.connect(db_uri, ssl=ctx)
        else:
            conn = await asyncpg.connect(db_uri)
        print("Connected! Running migration...")
        
        # Add title column
        try:
            await conn.execute("ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS title VARCHAR(255) DEFAULT 'New Workflow';")
            print("Added 'title' column.")
        except Exception as e:
            print(f"Error adding title: {e}")
            
        # Add messages column
        try:
            await conn.execute("ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS messages JSONB DEFAULT '[]'::jsonb;")
            print("Added 'messages' column.")
        except Exception as e:
            print(f"Error adding messages: {e}")
            
        await conn.close()
        print("Migration complete!")
    except Exception as e:
        print(f"Failed to connect or migrate: {e}")

if __name__ == "__main__":
    asyncio.run(run_migration())
