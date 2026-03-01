from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class AttendanceTrendPoint(BaseModel):
    date: str
    attendance_percent: float


class EngagementMetric(BaseModel):
    name: str
    value: float


class CodingActivityPoint(BaseModel):
    date: str
    problems_attempted: int
    problems_solved: int


class CodingPlatformSummary(BaseModel):
    """Per-platform coding stats shown on student dashboard."""
    platform_slug: str
    display_name: str
    username: str
    profile_url: str
    problems_solved: int = 0
    problems_attempted: int = 0
    active_days: int = 0
    difficulty_breakdown: Dict[str, int] = Field(default_factory=dict)


class RecoverySuggestion(BaseModel):
    title: str
    description: str


class StudentDashboardView(BaseModel):
    university_id: str
    student_id: str
    risk_level: str
    attendance_trend: List[AttendanceTrendPoint]
    lms_engagement: List[EngagementMetric]
    coding_activity: List[CodingActivityPoint]
    coding_platforms: List[CodingPlatformSummary] = []
    recovery_suggestions: List[RecoverySuggestion]


class ClassRiskBucket(BaseModel):
    level: str
    count: int


class AtRiskStudent(BaseModel):
    student_id: str
    name: str
    course_id: str
    risk_level: str
    explanation: Dict[str, float]


class TeacherDashboardView(BaseModel):
    university_id: str
    teacher_id: str
    course_id: Optional[str] = None
    total_students: int = 0
    class_risk_heatmap: List[ClassRiskBucket]
    at_risk_students: List[AtRiskStudent]
    page: int = 1
    page_size: int = 50
    total_at_risk: int = 0

