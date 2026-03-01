from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import uuid4


class Notification(BaseModel):
    id: str
    university_id: Optional[str] = None
    student_id: Optional[str] = None
    recipient_type: str
    recipient_id: str
    severity: str
    message: str
    created_at: datetime
    read: bool


class NotificationRuleInput(BaseModel):
    university_id: str
    student_id: str
    course_id: str
    risk_level: str
    academic_risk: dict
    dropout_probability: float
    recovery_probability: float


app = FastAPI(title="Notification Service")


# ── In-memory store (replace with PostgreSQL in production) ─
notifications_store: List[Notification] = []


@app.post("/evaluate", response_model=List[Notification])
async def evaluate(input: NotificationRuleInput):
    """Rule engine: auto-generate alerts based on risk thresholds."""
    generated = []

    # High academic risk  →  alert teacher
    if input.risk_level == "high" or input.dropout_probability > 0.7:
        generated.append(
            Notification(
                id=str(uuid4()),
                university_id=input.university_id,
                student_id=input.student_id,
                recipient_type="teacher",
                recipient_id="T001",
                severity="high",
                message=f"Student {input.student_id} is at high academic risk in {input.course_id}",
                created_at=datetime.utcnow(),
                read=False,
            )
        )

    # Medium risk  →  nudge student
    if input.risk_level == "medium":
        generated.append(
            Notification(
                id=str(uuid4()),
                university_id=input.university_id,
                student_id=input.student_id,
                recipient_type="student",
                recipient_id=input.student_id,
                severity="warning",
                message=f"Your academic pulse in {input.course_id} needs attention — consider attending office hours.",
                created_at=datetime.utcnow(),
                read=False,
            )
        )

    notifications_store.extend(generated)
    return generated


@app.get("/notifications", response_model=List[Notification])
async def list_notifications(
    recipient_type: str,
    recipient_id: str,
    university_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """Paginated notification list, optionally filtered by university."""
    result = [
        n for n in notifications_store
        if n.recipient_type == recipient_type
        and n.recipient_id == recipient_id
        and (university_id is None or n.university_id == university_id)
    ]
    # Newest first
    result.sort(key=lambda n: n.created_at, reverse=True)
    return result[offset : offset + limit]


@app.post("/notifications", response_model=Notification)
async def create_notification(notification: Notification):
    notifications_store.append(notification)
    return notification

