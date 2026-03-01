"""
Seed script to populate coding activity data in MongoDB.
Run this once to create test data for the Coding Activity Summary Card.
"""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import random

load_dotenv()


async def seed_coding_data():
    # Connect to MongoDB
    uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(uri)
    db = client[os.getenv("MONGO_DB_NAME", "academic_feature_store")]

    print("🔌 Connected to MongoDB")

    # Your student ID (from your signup)
    student_id = "2300031507@kluniversity.in"
    university_id = "UNI001"

    # ─────────────────────────────────────────────────────────────
    # 1. Create platform profiles (if not exists)
    # ─────────────────────────────────────────────────────────────
    profiles_collection = db["student_platform_profiles"]

    existing_profile = await profiles_collection.find_one({"student_id": student_id})

    if not existing_profile:
        await profiles_collection.insert_one({
            "university_id": university_id,
            "student_id": student_id,
            "profiles": {
                "leetcode": "mario_coder",
                "codechef": "mario_chef",
                "codeforces": "mario_cf"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        print("✅ Created platform profiles")
    else:
        print("ℹ️  Platform profiles already exist")

    # ─────────────────────────────────────────────────────────────
    # 2. Create coding activity events (last 60 days)
    # ─────────────────────────────────────────────────────────────
    coding_collection = db["coding_activity"]

    # Delete old test data
    await coding_collection.delete_many({"student_id": student_id})
    print("🗑️  Cleared old coding activity")

    platforms = [
        {"slug": "leetcode", "name": "LeetCode"},
        {"slug": "codechef", "name": "CodeChef"},
        {"slug": "codeforces", "name": "Codeforces"}
    ]

    difficulties = ["easy", "medium", "hard"]
    events = []

    # Generate random activity for last 60 days
    for days_ago in range(60):
        date = datetime.utcnow() - timedelta(days=days_ago)

        # Random chance of activity each day (70% chance)
        if random.random() < 0.7:
            # 1-5 problems per active day
            num_problems = random.randint(1, 5)

            for _ in range(num_problems):
                platform = random.choice(platforms)
                difficulty = random.choices(
                    difficulties,
                    weights=[0.5, 0.35, 0.15]  # More easy, fewer hard
                )[0]

                events.append({
                    "university_id": university_id,
                    "student_id": student_id,
                    "platform": platform["slug"],
                    "platform_name": platform["name"],
                    "event_type": "problem_solved",
                    "difficulty": difficulty,
                    "problem_id": f"prob_{random.randint(1000, 9999)}",
                    "problem_name": f"Sample Problem {random.randint(1, 500)}",
                    "timestamp": date.replace(
                        hour=random.randint(8, 22),
                        minute=random.randint(0, 59)
                    ),
                    "points": {"easy": 10, "medium": 25, "hard": 50}[difficulty]
                })

    # Insert all events
    if events:
        await coding_collection.insert_many(events)
        print(f"✅ Inserted {len(events)} coding activity events")

    # ─────────────────────────────────────────────────────────────
    # 3. Create aggregated coding stats
    # ─────────────────────────────────────────────────────────────
    stats_collection = db["coding_stats"]

    # Delete old stats
    await stats_collection.delete_many({"student_id": student_id})

    # Calculate stats from events
    platform_stats = {}
    for event in events:
        platform = event["platform"]
        if platform not in platform_stats:
            platform_stats[platform] = {
                "total": 0,
                "easy": 0,
                "medium": 0,
                "hard": 0,
                "points": 0
            }
        platform_stats[platform]["total"] += 1
        platform_stats[platform][event["difficulty"]] += 1
        platform_stats[platform]["points"] += event["points"]

    # Get unique active days
    active_dates = set()
    for event in events:
        active_dates.add(event["timestamp"].date())

    # Calculate streak
    streak = 0
    check_date = datetime.utcnow().date()
    while check_date in active_dates:
        streak += 1
        check_date -= timedelta(days=1)

    # Problems this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    this_week = len([e for e in events if e["timestamp"] > week_ago])

    # Problems last week (for comparison)
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    last_week = len([e for e in events if two_weeks_ago < e["timestamp"] <= week_ago])

    # Weekly activity (for heatmap)
    weekly_activity = [0] * 7  # Mon=0, Sun=6
    for event in events:
        if event["timestamp"] > week_ago:
            day_index = event["timestamp"].weekday()
            weekly_activity[day_index] += 1

    stats_doc = {
        "university_id": university_id,
        "student_id": student_id,
        "total_problems": len(events),
        "problems_this_week": this_week,
        "problems_last_week": last_week,
        "active_days_30": len([d for d in active_dates if d > (datetime.utcnow().date() - timedelta(days=30))]),
        "current_streak": streak,
        "longest_streak": max(streak, random.randint(streak, streak + 10)),
        "total_points": sum(p["points"] for p in platform_stats.values()),
        "platforms": [
            {
                "slug": slug,
                "name": {"leetcode": "LeetCode", "codechef": "CodeChef", "codeforces": "Codeforces"}[slug],
                "problems_solved": stats["total"],
                "easy": stats["easy"],
                "medium": stats["medium"],
                "hard": stats["hard"],
                "points": stats["points"]
            }
            for slug, stats in platform_stats.items()
        ],
        "weekly_activity": weekly_activity,
        "updated_at": datetime.utcnow()
    }

    await stats_collection.insert_one(stats_doc)
    print("✅ Created aggregated coding stats")

    # ─────────────────────────────────────────────────────────────
    # 4. Print summary
    # ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 CODING DATA SUMMARY")
    print("=" * 60)
    print(f"Student ID:        {student_id}")
    print(f"Total Problems:    {len(events)}")
    print(f"This Week:         {this_week}")
    print(f"Active Days (30d): {stats_doc['active_days_30']}")
    print(f"Current Streak:    {streak} days")
    print("-" * 60)
    print("Platform Breakdown:")
    for p in stats_doc["platforms"]:
        print(f"  {p['name']:12} → {p['problems_solved']:3} problems ({p['easy']}E / {p['medium']}M / {p['hard']}H)")
    print("-" * 60)
    print("Weekly Activity (Mon-Sun):")
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, count in enumerate(weekly_activity):
        bar = "█" * count + "░" * (5 - min(count, 5))
        print(f"  {days[i]}: {bar} {count}")
    print("=" * 60)

    client.close()
    print("\n✅ Done! Coding data seeded successfully.")
    print("👉 Now login to see the Coding Activity Card on your dashboard.")


if __name__ == "__main__":
    asyncio.run(seed_coding_data())