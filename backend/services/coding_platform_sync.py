"""
Service to simulate/fetch data from coding platforms (LeetCode, Codeforces, etc.).
In a real system, this would call external APIs or scrape public profiles.
For this project, it generates mock historical data and inserts it into MongoDB
so that dashboards show dynamic graphs immediately after a student links their profile.
"""

import random
import re
import httpx
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from backend.clients.mongo_client import get_db
from backend.settings import MongoCollections

async def validate_coding_profile(platform_slug: str, username: str) -> bool:
    """
    Validates if a coding profile exists by trying to fetch its basic stats.
    """
    if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
        return False
        
    if platform_slug == "leetcode":
        # Try to fetch real stats to see if user exists
        stats = await fetch_leetcode_stats(username)
        return stats is not None
        
    # For others, basic length check for now
    return len(username) >= 3

def extract_username(platform_slug: str, input_str: str) -> str:
    """Extracts username if the user provides a full URL instead of just username."""
    input_str = input_str.strip()
    if not input_str.startswith("http"):
        return input_str
        
    # Regex to pull the last part of common coding profile URLs
    patterns = {
        "leetcode": r"leetcode\.com/(?:u/)?([^/]+)",
        "codechef": r"codechef\.com/users/([^/]+)",
        "codeforces": r"codeforces\.com/profile/([^/]+)",
        "hackerrank": r"hackerrank\.com/([^/]+)",
        "geeksforgeeks": r"geeksforgeeks\.org/user/([^/]+)",
    }
    
    pattern = patterns.get(platform_slug)
    if pattern:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
            
    # Fallback: take the last segment
    return input_str.rstrip('/').split('/')[-1]

async def fetch_leetcode_stats(username: str):
    """Fetches real submission stats from LeetCode public GraphQL API."""
    url = "https://leetcode.com/graphql"
    query = """
    query userSessionProgress($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """
    async with httpx.AsyncClient() as client:
        try:
            # Use a more specific User-Agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            resp = await client.post(url, json={"query": query, "variables": {"username": username}}, headers=headers, timeout=15.0)
            
            if resp.status_code != 200:
                print(f"[leetcode] API returned {resp.status_code}: {resp.text}")
                return None
                
            data = resp.json()
            if "errors" in data:
                print(f"[leetcode] GraphQL errors for {username}: {data['errors']}")
                return None
                
            user = data.get("data", {}).get("matchedUser")
            if not user:
                print(f"[leetcode] User {username} not found.")
                return None
                
                stats = user.get("submitStats", {}).get("acSubmissionNum", [])
                total_solved = 0
                for s in stats:
                    if s["difficulty"] == "All":
                        total_solved = s["count"]
                return {"total_solved": total_solved}
        except Exception as e:
            print(f"[leetcode] Fetch failed for {username}: {e}")
    return None

async def sync_coding_platform_data(university_id: str, student_id: str, platform_slug: str, username: str):
    """
    Identifies and fetches real data for a linked profile.
    If real data fetching is not available for a platform, it remains empty
    instead of generating fake data.
    """
    db = get_db()
    now = datetime.now(timezone.utc)
    
    real_stats = None
    if platform_slug == "leetcode":
        real_stats = await fetch_leetcode_stats(username)
    
    if real_stats:
        # We have real data! 
        total_solved = real_stats.get("total_solved", 0)
        
        # Check if we already have a baseline or previous data
        last_event = await db[MongoCollections.RAW_EVENTS].find_one(
            {
                "meta.university_id": university_id, 
                "meta.student_id": student_id, 
                "platform": platform_slug
            },
            sort=[("timestamp", -1)]
        )
        
        # Determine if this is a baseline (first time) or an update
        is_baseline = last_event is None
        
        # If it's an update, calculate the delta
        delta_solved = 0
        if not is_baseline:
            # We want to find the last total solved to calculate delta
            # In our current schema, we might need to store the "cumulative_total" 
            # or just look at the last event's cumulative state.
            # Let's assume the feature store has the last known total.
            feature_doc = await db[MongoCollections.STUDENT_FEATURES].find_one(
                {"university_id": university_id, "student_id": student_id}
            )
            last_total = feature_doc.get("total_problems_solved", 0) if feature_doc else 0
            delta_solved = max(0, total_solved - last_total)
        
        # If no change and not baseline, don't create an event
        if delta_solved == 0 and not is_baseline:
            print(f"[sync] No change in LeetCode data for {username}. Skipping event.")
            return

        event = {
            "event_id": str(uuid4()),
            "event_type": "coding_activity",
            "timestamp": now,
            "meta": {
                "university_id": university_id,
                "student_id": student_id,
                "course_id": "CS_GENERIC",
            },
            "platform": platform_slug,
            "username": username,
            "problems_solved": total_solved if is_baseline else delta_solved,
            "problems_attempted": total_solved if is_baseline else delta_solved,
            "daily_active_days": 1,
            "is_real_data": True,
            "is_baseline": is_baseline
        }
        
        await db[MongoCollections.RAW_EVENTS].insert_one(event)
        
        # Update student_features with the NEW cumulative total
        await db[MongoCollections.STUDENT_FEATURES].update_one(
            {"university_id": university_id, "student_id": student_id},
            {
                "$set": {
                    "total_problems_solved": total_solved,
                    "total_problems_attempted": total_solved,
                    "updated_at": now
                }
            },
            upsert=True
        )
        print(f"[sync] Synchronized REAL LeetCode data for {username}: {total_solved} solved (Delta: {delta_solved}).")
    else:
        # If no real data can be fetched (or not implemented for this platform), 
        # we do NOT generate fake data anymore.
        print(f"[sync] No real data available for {platform_slug} user {username}. Skipping mock generation.")
