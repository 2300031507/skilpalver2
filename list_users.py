import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def run():
    client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
    db = client[os.getenv('MONGO_DB_NAME', 'academic_feature_store')]
    
    print("--- Students ---")
    async for user in db.users_students.find({}, {"password_hash": 0}):
        print(user)
        
    print("\n--- Admins ---")
    async for user in db.users_admins.find({}, {"password_hash": 0}):
        print(user)
        
    client.close()

if __name__ == "__main__":
    asyncio.run(run())
