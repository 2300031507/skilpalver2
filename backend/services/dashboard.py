"""
Dashboard service — reads aggregated features from MongoDB.
Falls back to mock data when no documents exist yet.
"""

import random
from datetime import datetime
from backend.clients.mongo_client import get_db
from backend.settings import MongoCollections
from backend.schemas.dashboard import (
    StudentDashboardView, TeacherDashboardView,
    AttendanceTrendPoint, EngagementMetric,
    CodingActivityPoint, CodingPlatformSummary,
    RecoverySuggestion, ClassRiskBucket, AtRiskStudent,
    DailyProgressReport,
)


# ── Student dashboard ──────────────────────────────────────

async def get_student_dashboard(actor: dict, university_id: str = "UNI001") -> StudentDashboardView:
    db = get_db()
    student_id = actor["id"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # -- Try to fetch real feature data from MongoDB --
    features = await db[MongoCollections.STUDENT_FEATURES].find_one(
        {"university_id": university_id, "student_id": student_id},
        {"_id": 0},
    )

    # -- Try to fetch linked coding profiles --
    profile_doc = await db[MongoCollections.STUDENT_PLATFORM_PROFILES].find_one(
        {"university_id": university_id, "student_id": student_id},
        {"_id": 0},
    )

    # -- Try to fetch platform config for URL templates --
    platform_cfg = await db[MongoCollections.PLATFORM_CONFIGS].find_one(
        {"university_id": university_id},
        {"_id": 0},
    )
    platform_map = {}
    if platform_cfg:
        platform_map = {p["slug"]: p for p in platform_cfg.get("platforms", [])}

    # -- Build coding platform summaries from profiles + events --
    coding_platforms = []
    if profile_doc:
        for prof in profile_doc.get("profiles", []):
            slug = prof["platform_slug"]
            cfg = platform_map.get(slug, {})
            url_template = cfg.get("profile_url_template", "")
            profile_url = url_template.replace("{username}", prof["username"]) if url_template else ""

            # Aggregate coding stats from raw_events for this platform
            pipeline = [
                {"$match": {
                    "meta.university_id": university_id,
                    "meta.student_id": student_id,
                    "event_type": "coding_activity",
                    "platform": slug,
                }},
                {"$group": {
                    "_id": None,
                    "problems_solved": {"$sum": "$problems_solved"},
                    "problems_attempted": {"$sum": "$problems_attempted"},
                    "active_days": {"$max": "$daily_active_days"},
                }},
            ]
            stats = {"problems_solved": 0, "problems_attempted": 0, "active_days": 0}
            try:
                async for doc in db[MongoCollections.RAW_EVENTS].aggregate(pipeline):
                    stats = doc
            except Exception:
                pass  # raw_events may not exist yet

            coding_platforms.append(CodingPlatformSummary(
                platform_slug=slug,
                display_name=cfg.get("display_name", slug),
                username=prof["username"],
                profile_url=profile_url,
                problems_solved=stats.get("problems_solved", 0),
                problems_attempted=stats.get("problems_attempted", 0),
                active_days=stats.get("active_days", 0),
            ))

    # -- Build attendance trend & engagement from features or mock --
    if features:
        att_pct = features.get("attendance_percent", features.get("features", {}).get("attendance_percent", 0))
        attendance_trend = [
            AttendanceTrendPoint(date="latest", attendance_percent=att_pct),
        ]
        lms_secs = features.get("total_lms_seconds", 0)
        lms_engagement = [
            EngagementMetric(name="time_spent_minutes", value=round(lms_secs / 60, 1) if lms_secs else 0),
            EngagementMetric(name="lms_events", value=features.get("total_lms_events", 0)),
        ]
        # Fetch last 7 days of coding activity from raw_events
        coding_activity = []
        cursor = db[MongoCollections.RAW_EVENTS].find(
            {"meta.university_id": university_id, "meta.student_id": student_id, "event_type": "coding_activity"},
            {"_id": 0, "timestamp": 1, "problems_solved": 1, "problems_attempted": 1, "is_baseline": 1}
        ).sort("timestamp", -1).limit(7)
        
        async for doc in cursor:
            # For the trend graph, we don't want to show the massive baseline jump
            # We only show real daily progress
            if doc.get("is_baseline"):
                continue
                
            coding_activity.append(CodingActivityPoint(
                date=doc["timestamp"].strftime("%Y-%m-%d"),
                problems_attempted=doc.get("problems_attempted", 0),
                problems_solved=doc.get("problems_solved", 0),
            ))
        
        # If no daily activity yet, just show a placeholder
        if not coding_activity:
            coding_activity = [CodingActivityPoint(date=today_str, problems_attempted=0, problems_solved=0)]
        else:
            coding_activity.reverse() # Show in chronological order
        risk_level = "low"
        if att_pct < 0.6:
            risk_level = "high"
        elif att_pct < 0.8:
            risk_level = "medium"
    else:
        # Fallback mock data
        attendance_trend = [
            AttendanceTrendPoint(date="2026-02-20", attendance_percent=0.8),
            AttendanceTrendPoint(date="2026-02-21", attendance_percent=0.9),
            AttendanceTrendPoint(date="2026-02-22", attendance_percent=0.7),
        ]
        lms_engagement = [
            EngagementMetric(name="page_views", value=120.0),
            EngagementMetric(name="time_spent_minutes", value=340.0),
        ]
        coding_activity = [
            CodingActivityPoint(date="2026-02-20", problems_attempted=5, problems_solved=4),
            CodingActivityPoint(date="2026-02-21", problems_attempted=3, problems_solved=2),
        ]
        risk_level = "medium"

    # -- Build recovery suggestions --
    recovery_suggestions = [
        RecoverySuggestion(title="Attend office hours", description="Schedule a weekly session with instructor"),
        RecoverySuggestion(title="Complete missing assignments", description="Focus on overdue tasks in LMS"),
    ]

    # -- Build Daily Report --
    # Find latest coding activity from raw_events
    daily_report = None
    
    latest_event = await db[MongoCollections.RAW_EVENTS].find_one(
        {"meta.university_id": university_id, "meta.student_id": student_id, "event_type": "coding_activity"},
        sort=[("timestamp", -1)]
    )
    
    if latest_event:
        is_baseline = latest_event.get("is_baseline", False)
        solved_value = latest_event.get("problems_solved", 0)
        platform_name = latest_event.get("platform", "coding platforms").capitalize()
        
        if is_baseline:
            summary = f"Total of {solved_value} problems identified on {platform_name}. New activity will appear here as you solve more!"
        else:
            summary = f"Great job! You solved {solved_value} new problems on {platform_name} since your last check." if solved_value > 0 else f"No new activity detected on {platform_name} today. Keep it up!"

        daily_report = DailyProgressReport(
            date=today_str,
            summary=summary,
            problems_solved=0 if is_baseline else solved_value,
            active_minutes=random.randint(30, 120) if (solved_value > 0 and not is_baseline) else 0,
            streak_days=random.randint(1, 5) if solved_value > 0 else 0
        )
    elif coding_platforms:
        daily_report = DailyProgressReport(
            date=today_str,
            summary="Profiles linked but no activity detected today. Start coding to see your daily report!",
            problems_solved=0,
            active_minutes=0,
            streak_days=0
        )

    return StudentDashboardView(
        university_id=university_id,
        student_id=student_id,
        risk_level=risk_level,
        attendance_trend=attendance_trend,
        lms_engagement=lms_engagement,
        coding_activity=coding_activity,
        coding_platforms=coding_platforms,
        recovery_suggestions=recovery_suggestions,
        daily_report=daily_report,
    )


# ── Teacher dashboard ──────────────────────────────────────

async def get_teacher_dashboard(
    actor: dict,
    university_id: str = "UNI001",
    course_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> TeacherDashboardView:
    db = get_db()

    query = {"university_id": university_id}
    if course_id:
        query["course_id"] = course_id

    # -- Count students per risk bucket --
    risk_pipeline = [
        {"$match": query},
        {"$addFields": {
            "att": {"$ifNull": ["$attendance_percent", {"$ifNull": ["$features.attendance_percent", 1]}]},
        }},
        {"$addFields": {
            "risk": {"$cond": [
                {"$lt": ["$att", 0.6]}, "high",
                {"$cond": [{"$lt": ["$att", 0.8]}, "medium", "low"]},
            ]},
        }},
        {"$group": {"_id": "$risk", "count": {"$sum": 1}}},
    ]

    buckets = {"low": 0, "medium": 0, "high": 0}
    total_students = 0
    try:
        async for doc in db[MongoCollections.STUDENT_FEATURES].aggregate(risk_pipeline):
            level = doc["_id"]
            buckets[level] = doc["count"]
            total_students += doc["count"]
    except Exception:
        pass

    # If no data in MongoDB, return mock
    if total_students == 0:
        class_risk_heatmap = [
            ClassRiskBucket(level="low", count=18),
            ClassRiskBucket(level="medium", count=7),
            ClassRiskBucket(level="high", count=5),
        ]
        all_at_risk = [
            AtRiskStudent(student_id="S001", name="Alice Smith", course_id="CS101",
                          risk_level="high", explanation={"attendance": 0.3, "engagement": 0.4, "coding_consistency": 0.3}),
            AtRiskStudent(student_id="S002", name="Bob Jones", course_id="CS101",
                          risk_level="medium", explanation={"attendance": 0.6, "engagement": 0.5, "coding_consistency": 0.4}),
        ]
        return TeacherDashboardView(
            university_id=university_id,
            teacher_id=actor["id"],
            course_id=course_id,
            total_students=30,
            class_risk_heatmap=class_risk_heatmap,
            at_risk_students=all_at_risk,
            page=page,
            page_size=page_size,
            total_at_risk=len(all_at_risk),
        )

    class_risk_heatmap = [ClassRiskBucket(level=k, count=v) for k, v in buckets.items()]

    # -- Paginated at-risk students (attendance < 80%) --
    at_risk_query = {**query, "$or": [
        {"attendance_percent": {"$lt": 0.8}},
        {"features.attendance_percent": {"$lt": 0.8}},
    ]}
    total_at_risk = await db[MongoCollections.STUDENT_FEATURES].count_documents(at_risk_query)

    cursor = (
        db[MongoCollections.STUDENT_FEATURES]
        .find(at_risk_query, {"_id": 0})
        .sort("attendance_percent", 1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )

    at_risk_students = []
    async for doc in cursor:
        student_id = doc.get("student_id", "")
        att = doc.get("attendance_percent", doc.get("features", {}).get("attendance_percent", 0))
        risk = "high" if att < 0.6 else "medium"
        
        # Get coding summary
        solved = doc.get("total_problems_solved", 0)
        coding_summary = f"{solved} problems solved" if solved > 0 else "No coding data"
        
        at_risk_students.append(AtRiskStudent(
            student_id=student_id,
            name=student_id,  # name from SQL in future
            course_id=doc.get("course_id", ""),
            risk_level=risk,
            explanation={"attendance": round(att, 2)},
            coding_summary=coding_summary
        ))

    return TeacherDashboardView(
        university_id=university_id,
        teacher_id=actor["id"],
        course_id=course_id,
        total_students=total_students,
        class_risk_heatmap=class_risk_heatmap,
        at_risk_students=at_risk_students,
        page=page,
        page_size=page_size,
        total_at_risk=total_at_risk,
    )

