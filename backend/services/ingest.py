from uuid import uuid4
from typing import List
from backend.schemas.events import (
    AttendanceEvent, LMSActivityEvent, CodingActivityEvent,
    EventIngestResponse, BulkAttendanceRequest, BulkLMSRequest,
    BulkCodingRequest, BulkIngestResponse,
)
from backend.services.kafka import producer
from backend.settings import KafkaTopics, BULK_INGEST_MAX_EVENTS


# ── Single-event ingest (unchanged) ────────────────────────

async def ingest_attendance_event(event: AttendanceEvent, actor: dict) -> EventIngestResponse:
    event_id = str(uuid4())
    payload = event.dict()
    payload["event_id"] = event_id
    payload["actor_id"] = actor["id"]
    producer.send(KafkaTopics.ATTENDANCE, payload)
    return EventIngestResponse(status="accepted", event_id=event_id)


async def ingest_lms_event(event: LMSActivityEvent, actor: dict) -> EventIngestResponse:
    event_id = str(uuid4())
    payload = event.dict()
    payload["event_id"] = event_id
    payload["actor_id"] = actor["id"]
    producer.send(KafkaTopics.LMS_ACTIVITY, payload)
    return EventIngestResponse(status="accepted", event_id=event_id)


async def ingest_coding_event(event: CodingActivityEvent, actor: dict) -> EventIngestResponse:
    event_id = str(uuid4())
    payload = event.dict()
    payload["event_id"] = event_id
    payload["actor_id"] = actor["id"]
    producer.send(KafkaTopics.CODING_ACTIVITY, payload)
    return EventIngestResponse(status="accepted", event_id=event_id)


# ── Bulk ingest  ─  fan-out to Kafka in one go ─────────────

async def _bulk_ingest(events: list, topic: str, actor: dict) -> BulkIngestResponse:
    """
    Send up to BULK_INGEST_MAX_EVENTS to Kafka in a tight loop.
    In production, replace with producer.send_batch() or
    Kafka transactions for exactly-once semantics.
    """
    job_id = str(uuid4())
    accepted = 0
    rejected = 0
    errors: List[str] = []

    for idx, event in enumerate(events[:BULK_INGEST_MAX_EVENTS]):
        try:
            payload = event.dict()
            payload["event_id"] = str(uuid4())
            payload["actor_id"] = actor["id"]
            payload["bulk_job_id"] = job_id
            producer.send(topic, payload)
            accepted += 1
        except Exception as exc:
            rejected += 1
            errors.append(f"row {idx}: {str(exc)}")

    return BulkIngestResponse(
        status="accepted",
        job_id=job_id,
        total_events=len(events),
        accepted=accepted,
        rejected=rejected,
        errors=errors[:50],  # cap error list to keep response small
    )


async def bulk_ingest_attendance(req: BulkAttendanceRequest, actor: dict) -> BulkIngestResponse:
    return await _bulk_ingest(req.events, KafkaTopics.ATTENDANCE, actor)


async def bulk_ingest_lms(req: BulkLMSRequest, actor: dict) -> BulkIngestResponse:
    return await _bulk_ingest(req.events, KafkaTopics.LMS_ACTIVITY, actor)


async def bulk_ingest_coding(req: BulkCodingRequest, actor: dict) -> BulkIngestResponse:
    return await _bulk_ingest(req.events, KafkaTopics.CODING_ACTIVITY, actor)

