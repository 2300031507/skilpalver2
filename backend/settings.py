class KafkaTopics:
    ATTENDANCE = "student-attendance-events"
    LMS_ACTIVITY = "student-lms-activity-events"
    CODING_ACTIVITY = "student-coding-activity-events"
    STUDENT_FEATURES = "student-feature-updates"


class MongoCollections:
    RAW_EVENTS = "raw_events"
    STUDENT_FEATURES = "student_features"
    PLATFORM_CONFIGS = "platform_configs"
    STUDENT_PLATFORM_PROFILES = "student_platform_profiles"
    BULK_INGEST_JOBS = "bulk_ingest_jobs"


class SqlTables:
    UNIVERSITIES = "universities"
    STUDENTS = "students"
    COURSES = "courses"
    ENROLLMENTS = "enrollments"
    RISK_PREDICTIONS = "risk_predictions"
    NOTIFICATIONS = "notifications"


# ── Defaults ──────────────────────────────────────────────
# Well-known coding platforms that admins can pick from
DEFAULT_PLATFORM_REGISTRY = [
    {
        "slug": "leetcode",
        "display_name": "LeetCode",
        "base_url": "https://leetcode.com",
        "profile_url_template": "https://leetcode.com/u/{username}",
    },
    {
        "slug": "codechef",
        "display_name": "CodeChef",
        "base_url": "https://www.codechef.com",
        "profile_url_template": "https://www.codechef.com/users/{username}",
    },
    {
        "slug": "codeforces",
        "display_name": "Codeforces",
        "base_url": "https://codeforces.com",
        "profile_url_template": "https://codeforces.com/profile/{username}",
    },
    {
        "slug": "hackerrank",
        "display_name": "HackerRank",
        "base_url": "https://www.hackerrank.com",
        "profile_url_template": "https://www.hackerrank.com/profile/{username}",
    },
    {
        "slug": "hackerearth",
        "display_name": "HackerEarth",
        "base_url": "https://www.hackerearth.com",
        "profile_url_template": "https://www.hackerearth.com/@{username}",
    },
    {
        "slug": "geeksforgeeks",
        "display_name": "GeeksforGeeks",
        "base_url": "https://www.geeksforgeeks.org",
        "profile_url_template": "https://www.geeksforgeeks.org/user/{username}",
    },
]

# Bulk ingest limits
BULK_INGEST_MAX_EVENTS = 10_000  # max events per single batch request

