from typing import List
from datetime import datetime
from uuid import uuid4
import httpx
from backend.schemas.notifications import Notification, NotificationCreateRequest


NOTIFICATIONS_BASE_URL = "http://localhost:8002"


async def list_notifications_for_actor(actor: dict) -> List[Notification]:
    try:
        async with httpx.AsyncClient(base_url=NOTIFICATIONS_BASE_URL) as client:
            response = await client.get(
                "/notifications",
                params={"recipient_type": actor["role"], "recipient_id": actor["id"]},
                timeout=2.0,
            )
            response.raise_for_status()
            items = response.json()
        return [Notification(**item) for item in items]
    except Exception as e:
        print(f"Notification service unreachable: {e}")
        return []


async def create_manual_notification(payload: NotificationCreateRequest, actor: dict) -> Notification:
    notification = Notification(
        id=str(uuid4()),
        student_id=payload.student_id,
        recipient_type=payload.recipient_type,
        recipient_id=payload.recipient_id,
        severity=payload.severity,
        message=payload.message,
        created_at=datetime.utcnow(),
        read=False,
    )
    async with httpx.AsyncClient(base_url=NOTIFICATIONS_BASE_URL) as client:
        response = await client.post("/notifications", json=notification.dict(), timeout=5.0)
        response.raise_for_status()
        data = response.json()
    return Notification(**data)

