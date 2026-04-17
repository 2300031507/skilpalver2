"""Quick test: verify MongoDB Atlas connection and seed initial collections."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()


async def test():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME", "academic_feature_store")

    print(f"Connecting to: {db_name} ...")
    client = AsyncIOMotorClient(uri)

    # Ping
    result = await client.admin.command("ping")
    print(f"Connected! Ping: {result}")

    db = client[db_name]

    # List existing collections
    collections = await db.list_collection_names()
    print(f"Existing collections: {collections}")

    # Create collections if they don't exist
    needed = [
        "raw_events", "student_features", "platform_configs",
        "student_platform_profiles", "bulk_ingest_jobs",
        "users_students", "users_teachers", "users_admins",
    ]
    for name in needed:
        if name not in collections:
            await db.create_collection(name)
            print(f"  Created: {name}")
        else:
            print(f"  Exists:  {name}")

    # Create indexes
    await db.platform_configs.create_index("university_id", unique=True)
    await db.student_platform_profiles.create_index(
        [("university_id", 1), ("student_id", 1)], unique=True
    )
    await db.student_features.create_index(
        [("university_id", 1), ("student_id", 1), ("course_id", 1)], unique=True
    )
    await db.users_students.create_index("email", unique=True)
    await db.users_teachers.create_index("email", unique=True)
    await db.users_admins.create_index("email", unique=True)
    print("Indexes created.")

    # Count docs
    for name in needed:
        count = await db[name].count_documents({})
        print(f"  {name}: {count} docs")

    client.close()
    print("\nMongoDB is ready!")


asyncio.run(test())
