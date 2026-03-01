"""
Router for bulk event ingestion.

Accepts up to 10 000 events per call so admins can upload
attendance CSVs / LMS exports / coding dumps without per-row round trips.
"""

from fastapi import APIRouter, Depends
from backend.schemas.events import (
    BulkAttendanceRequest, BulkLMSRequest, BulkCodingRequest,
    BulkIngestResponse,
)
from backend.services.ingest import (
    bulk_ingest_attendance, bulk_ingest_lms, bulk_ingest_coding,
)
from backend.services.auth import get_current_actor

router = APIRouter(tags=["bulk-ingest"])


@router.post("/bulk/attendance", response_model=BulkIngestResponse)
async def bulk_attendance(body: BulkAttendanceRequest, actor=Depends(get_current_actor)):
    """Upload up to 10 000 attendance events in one call."""
    return await bulk_ingest_attendance(body, actor)


@router.post("/bulk/lms-activity", response_model=BulkIngestResponse)
async def bulk_lms(body: BulkLMSRequest, actor=Depends(get_current_actor)):
    """Upload up to 10 000 LMS activity events in one call."""
    return await bulk_ingest_lms(body, actor)


@router.post("/bulk/coding-activity", response_model=BulkIngestResponse)
async def bulk_coding(body: BulkCodingRequest, actor=Depends(get_current_actor)):
    """Upload up to 10 000 coding activity events in one call."""
    return await bulk_ingest_coding(body, actor)
