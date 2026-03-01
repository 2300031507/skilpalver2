from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class AttendanceEvent(BaseModel):
    student_id: str
    university_id: str
    course_id: str
    date: datetime
    present: bool
    source: str = Field(default="manual")


class LMSActivityEvent(BaseModel):
    student_id: str
    university_id: str
    course_id: str
    timestamp: datetime
    action: str
    duration_seconds: int
    platform: str = Field(default="canvas") # e.g., Canvas, Moodle, Blackboard


class CodingActivityEvent(BaseModel):
    student_id: str
    university_id: str
    course_id: str
    timestamp: datetime
    platform: str # LeetCode, CodeChef, CodeForces
    username: str # Platform-specific username
    problems_attempted: int
    problems_solved: int
    daily_active_days: int # How many days active in a streak
    total_problems_solved: int
    difficulty_breakdown: dict = Field(default_factory=dict) # e.g. {"easy": 10, "medium": 5, "hard": 1}


class EventIngestResponse(BaseModel):
    status: str
    event_id: str


# ── Bulk Ingest ─────────────────────────────────────────────
# Accepts up to 10 000 events in one HTTP call so that admins
# can upload a CSV/Excel dump without per-row round trips.

class BulkAttendanceRequest(BaseModel):
    university_id: str
    events: List[AttendanceEvent] = Field(..., max_length=10_000)


class BulkLMSRequest(BaseModel):
    university_id: str
    events: List[LMSActivityEvent] = Field(..., max_length=10_000)


class BulkCodingRequest(BaseModel):
    university_id: str
    events: List[CodingActivityEvent] = Field(..., max_length=10_000)


class BulkIngestResponse(BaseModel):
    status: str              # "accepted"
    job_id: str              # track the batch
    total_events: int
    accepted: int
    rejected: int
    errors: List[str] = []

