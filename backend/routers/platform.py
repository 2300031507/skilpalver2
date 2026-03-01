"""
Router for coding-platform configuration (admin) and student profile linking.

Endpoints
─────────
GET  /platforms/registry                 → global list of known platforms (dropdown)
GET  /platforms/config/{university_id}   → read university platform config
PUT  /platforms/config                   → admin sets/updates platform config
GET  /platforms/profile/{uni}/{student}  → read one student's linked profiles
POST /platforms/profile/link             → student links their usernames
POST /platforms/profile/bulk-link        → admin bulk-uploads student links
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas.platform import (
    PlatformConfigIn, PlatformConfigOut,
    LinkPlatformRequest, StudentPlatformProfileOut,
    BulkLinkRequest, BulkLinkResponse,
)
from backend.services.platform import (
    get_platform_registry,
    upsert_platform_config, get_platform_config,
    link_student_profiles, get_student_profiles,
    bulk_link_profiles,
)
from backend.services.auth import get_current_actor

router = APIRouter(tags=["platforms"])


# ── Global registry (read-only) ────────────────────────────

@router.get("/platforms/registry")
async def list_platform_registry():
    """
    Returns a list of well-known coding platforms.
    Admin UI uses this to show a dropdown when configuring their university.
    """
    return get_platform_registry()


# ── University platform config (admin) ─────────────────────

@router.get("/platforms/config/{university_id}", response_model=PlatformConfigOut)
async def read_platform_config(university_id: str):
    cfg = await get_platform_config(university_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="No platform config for this university")
    return cfg


@router.put("/platforms/config", response_model=PlatformConfigOut)
async def set_platform_config(body: PlatformConfigIn, actor=Depends(get_current_actor)):
    return await upsert_platform_config(body, actor)


# ── Student profile linking ────────────────────────────────

@router.get(
    "/platforms/profile/{university_id}/{student_id}",
    response_model=StudentPlatformProfileOut,
)
async def read_student_profiles(university_id: str, student_id: str):
    profile = await get_student_profiles(university_id, student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="No linked profiles found")
    return profile


@router.post("/platforms/profile/link", response_model=StudentPlatformProfileOut)
async def link_profiles(body: LinkPlatformRequest, actor=Depends(get_current_actor)):
    """Student submits their platform usernames (one or many at once)."""
    return await link_student_profiles(body)


@router.post("/platforms/profile/bulk-link", response_model=BulkLinkResponse)
async def bulk_link(body: BulkLinkRequest, actor=Depends(get_current_actor)):
    """
    Admin bulk-uploads a JSON / parsed-CSV of student ↔ platform links.
    Accepts up to 10 000 rows per call.
    """
    return await bulk_link_profiles(body)
