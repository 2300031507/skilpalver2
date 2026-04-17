import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

DEFAULT_PLATFORMS = [
    {
        "slug": "leetcode",
        "display_name": "LeetCode",
        "base_url": "https://leetcode.com",
        "profile_url_template": "https://leetcode.com/u/{username}",
        "active": True
    },
    {
        "slug": "codechef",
        "display_name": "CodeChef",
        "base_url": "https://www.codechef.com",
        "profile_url_template": "https://www.codechef.com/users/{username}",
        "active": True
    },
    {
        "slug": "codeforces",
        "display_name": "Codeforces",
        "base_url": "https://codeforces.com",
        "profile_url_template": "https://codeforces.com/profile/{username}",
        "active": True
    }
]

async def seed_platforms():
    client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
    db = client[os.getenv('MONGO_DB_NAME', 'academic_feature_store')]
    
    university_id = "UNI001"
    
    existing = await db.platform_configs.find_one({"university_id": university_id})
    
    if not existing:
        print(f"Seeding default platforms for {university_id}...")
        await db.platform_configs.insert_one({
            "university_id": university_id,
            "platforms": DEFAULT_PLATFORMS,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "system_seed"
        })
        print("Done!")
    else:
        print(f"Platforms already configured for {university_id}.")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_platforms())
