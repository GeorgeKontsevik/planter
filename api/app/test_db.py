# app/test_db.py

import asyncio
from sqlalchemy import text  # Import the 'text' construct
from .database import engine

async def test_connection():
    async with engine.connect() as conn:
        # Wrap the SQL string with 'text'
        result = await conn.execute(text("SELECT 1"))
        value = result.scalar()
        print(f"Database connection successful, result: {value}")

if __name__ == "__main__":
    asyncio.run(test_connection())