import requests
from datetime import datetime


BASE_URL = "http://localhost:8000/api"
HEADERS = {"X-Actor-Id": "S001", "X-Actor-Role": "student"}


def post(path: str, payload: dict):
    response = requests.post(f"{BASE_URL}{path}", json=payload, headers=HEADERS, timeout=5.0)
    response.raise_for_status()
    return response.json()


def send_sample_events():
    today = datetime.utcnow().date().isoformat()
    student_id = "S001"
    university_id = "UNI-XYZ-01"

    attendance = {
        "student_id": student_id,
        "university_id": university_id,
        "course_id": "CS101",
        "date": today,
        "present": True,
        "source": "automated_rfid",
    }
    lms = {
        "student_id": student_id,
        "university_id": university_id,
        "course_id": "CS101",
        "timestamp": datetime.utcnow().isoformat(),
        "action": "assignment_submission",
        "duration_seconds": 3600,
        "platform": "canvas"
    }
    
    # Simulate multiple platform data
    platforms = [
        {"name": "leetcode", "user": "user_s001_lc", "solved": 5, "streak": 12},
        {"name": "codechef", "user": "user_s001_cc", "solved": 2, "streak": 4},
        {"name": "codeforces", "user": "user_s001_cf", "solved": 1, "streak": 0}
    ]

    for p in platforms:
        coding = {
            "student_id": student_id,
            "university_id": university_id,
            "course_id": "DSA-Advanced",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": p["name"],
            "username": p["user"],
            "problems_attempted": p["solved"] + 1,
            "problems_solved": p["solved"],
            "daily_active_days": p["streak"],
            "total_problems_solved": 150 + p["solved"],
            "difficulty_breakdown": {"easy": p["solved"], "medium": 0, "hard": 0}
        }
        print(f"Sending {p['name']} data: {post('/coding-activity', coding)}")

    print(f"Attendance recorded: {post('/attendance', attendance)}")
    print(f"LMS activity recorded: {post('/lms-activity', lms)}")


if __name__ == "__main__":
    send_sample_events()

