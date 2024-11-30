# app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables.")

# Create asynchronous engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to False in production for less verbose logs
    future=True,
)

# Create sessionmaker factory
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
Base = declarative_base()
# dependencies.py or database.py


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()