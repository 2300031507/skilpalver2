"""
Async MongoDB client using Motor.

Usage:
    from backend.clients.mongo_client import connect_mongo, close_mongo, get_db

    # On startup
    await connect_mongo()

    # In any service
    db = get_db()
    doc = await db["student_features"].find_one({"student_id": "S001"})

    # On shutdown
    await close_mongo()
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_mongo() -> None:
    """Call once during FastAPI startup."""
    global _client, _db
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "academic_feature_store")

    _client = AsyncIOMotorClient(uri)
    _db = _client[db_name]

    # Verify connectivity
    await _client.admin.command("ping")
    print(f"[mongo] Connected to '{db_name}'")


async def close_mongo() -> None:
    """Call once during FastAPI shutdown."""
    global _client
    if _client:
        _client.close()
        print("[mongo] Connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """Return the database handle. Raises if not connected."""
    if _db is None:
        raise RuntimeError("MongoDB not connected – call connect_mongo() first")
    return _db
