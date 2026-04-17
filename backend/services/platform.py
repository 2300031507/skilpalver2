"""
Service layer for platform_configs and student_platform_profiles.
All data persisted to MongoDB via Motor (async driver).
"""

from __future__ import annotations
from datetime import datetime, timezone
from copy import deepcopy
from typing import Dict, List, Optional
from collections import defaultdict

from backend.clients.mongo_client import get_db
from backend.settings import MongoCollections, DEFAULT_PLATFORM_REGISTRY
from backend.schemas.platform import (
    PlatformConfigIn, PlatformConfigOut, PlatformEntry,
    LinkPlatformRequest, UnlinkPlatformRequest, StudentPlatformProfileOut, StudentProfileEntry,
    BulkLinkRequest, BulkLinkResponse,
)
from backend.services.coding_platform_sync import (
    sync_coding_platform_data, extract_username, validate_coding_profile
)


# ── Global registry ────────────────────────────────────────

def get_platform_registry() -> list:
    """Return known platforms so admin UI can show a dropdown."""
    return deepcopy(DEFAULT_PLATFORM_REGISTRY)


# ── Platform config (admin) ────────────────────────────────

async def upsert_platform_config(
    data: PlatformConfigIn, actor: dict
) -> PlatformConfigOut:
    """Admin sets which platforms their university uses."""
    db = get_db()
    doc = {
        "university_id": data.university_id,
        "platforms": [p.dict() for p in data.platforms],
        "updated_at": datetime.now(timezone.utc),
        "updated_by": actor.get("id", "unknown"),
    }
    await db[MongoCollections.PLATFORM_CONFIGS].update_one(
        {"university_id": data.university_id},
        {"$set": doc},
        upsert=True,
    )
    return PlatformConfigOut(**doc)


async def get_platform_config(university_id: str) -> Optional[PlatformConfigOut]:
    db = get_db()
    doc = await db[MongoCollections.PLATFORM_CONFIGS].find_one(
        {"university_id": university_id}, {"_id": 0}
    )
    if doc:
        return PlatformConfigOut(**doc)
    return None


async def get_active_platforms(university_id: str) -> List[PlatformEntry]:
    """Return only active platforms for a university."""
    db = get_db()
    doc = await db[MongoCollections.PLATFORM_CONFIGS].find_one(
        {"university_id": university_id}, {"_id": 0}
    )
    if not doc:
        return []
    return [
        PlatformEntry(**p) for p in doc.get("platforms", []) if p.get("active", True)
    ]


# ── Student profile linking ────────────────────────────────

async def link_student_profiles(
    req: LinkPlatformRequest,
) -> StudentPlatformProfileOut:
    """
    Student links their platform usernames.
    Merge-upsert: existing slugs are updated, new slugs are appended.
    """
    db = get_db()
    col = db[MongoCollections.STUDENT_PLATFORM_PROFILES]

    existing = await col.find_one(
        {"university_id": req.university_id, "student_id": req.student_id},
        {"_id": 0},
    )
    if not existing:
        existing = {
            "university_id": req.university_id,
            "student_id": req.student_id,
            "profiles": [],
        }

    # Build a slug → entry map for fast merge
    slug_map = {p["platform_slug"]: p for p in existing["profiles"]}
    now = datetime.now(timezone.utc)
    
    for entry in req.profiles:
        # 1. Extract username if they pasted a URL
        actual_username = extract_username(entry.platform_slug, entry.username)
        
        # 2. Validate the profile (real check)
        is_valid = await validate_coding_profile(entry.platform_slug, actual_username)
        if not is_valid:
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST, 
                 detail=f"The {entry.platform_slug} profile '{actual_username}' does not exist or is invalid. Please check the URL/Username."
             )

        slug_map[entry.platform_slug] = {
            "platform_slug": entry.platform_slug,
            "username": actual_username,
            "linked_at": now.isoformat(),
            "verified": is_valid,
        }

    existing["profiles"] = list(slug_map.values())

    await col.update_one(
        {"university_id": req.university_id, "student_id": req.student_id},
        {"$set": existing},
        upsert=True,
    )

    # Trigger background sync for each newly linked/updated profile
    for entry in req.profiles:
        # In a real app, use BackgroundTasks or Celery
        try:
            await sync_coding_platform_data(
                req.university_id, req.student_id, 
                entry.platform_slug, entry.username
            )
        except Exception as e:
            print(f"[platform] Sync failed for {entry.platform_slug}: {e}")

    return StudentPlatformProfileOut(**existing)


async def unlink_student_profile(
    req: UnlinkPlatformRequest,
) -> StudentPlatformProfileOut:
    """
    Removes a platform link from the student's profiles.
    """
    db = get_db()
    col = db[MongoCollections.STUDENT_PLATFORM_PROFILES]

    await col.update_one(
        {"university_id": req.university_id, "student_id": req.student_id},
        {"$pull": {"profiles": {"platform_slug": req.platform_slug}}}
    )

    doc = await col.find_one(
        {"university_id": req.university_id, "student_id": req.student_id},
        {"_id": 0}
    )
    if not doc:
        return StudentPlatformProfileOut(
            university_id=req.university_id,
            student_id=req.student_id,
            profiles=[]
        )
    return StudentPlatformProfileOut(**doc)


async def get_student_profiles(
    university_id: str, student_id: str
) -> Optional[StudentPlatformProfileOut]:
    db = get_db()
    doc = await db[MongoCollections.STUDENT_PLATFORM_PROFILES].find_one(
        {"university_id": university_id, "student_id": student_id},
        {"_id": 0},
    )
    if doc:
        return StudentPlatformProfileOut(**doc)
    return None


# ── Bulk link (admin uploads CSV/JSON of student→platform) ─

async def bulk_link_profiles(req: BulkLinkRequest) -> BulkLinkResponse:
    """
    Process up to 10 000 rows in one call.
    Groups rows by student, then upserts each student's profile document.
    """
    grouped: Dict[str, List] = defaultdict(list)
    for row in req.rows:
        grouped[row.student_id].append(row)

    linked = 0
    skipped = 0
    errors: List[str] = []

    for student_id, rows in grouped.items():
        try:
            profiles = [
                StudentProfileEntry(
                    platform_slug=r.platform_slug,
                    username=r.username,
                    linked_at=datetime.now(timezone.utc),
                )
                for r in rows
            ]
            await link_student_profiles(
                LinkPlatformRequest(
                    university_id=req.university_id,
                    student_id=student_id,
                    profiles=profiles,
                )
            )
            linked += len(rows)
        except Exception as exc:
            skipped += len(rows)
            errors.append(f"student {student_id}: {exc}")

    return BulkLinkResponse(
        total=len(req.rows),
        linked=linked,
        skipped=skipped,
        errors=errors[:50],
    )
