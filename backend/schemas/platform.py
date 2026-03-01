"""Schemas for coding-platform configuration and student profile linking."""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Platform Config (admin-managed per university) ──────────

class PlatformEntry(BaseModel):
    """One coding platform that a university supports."""
    slug: str = Field(..., description="Unique machine key, e.g. 'leetcode'")
    display_name: str = Field(..., description="Human-readable name shown in UI")
    base_url: str = Field(..., description="Platform home page")
    profile_url_template: str = Field(
        ...,
        description="URL template with {username} placeholder, e.g. https://leetcode.com/u/{username}",
    )
    active: bool = True


class PlatformConfigIn(BaseModel):
    """Body sent by admin to set / update the platform list for their university."""
    university_id: str
    platforms: List[PlatformEntry]


class PlatformConfigOut(BaseModel):
    """Returned when reading platform config."""
    university_id: str
    platforms: List[PlatformEntry]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


# ── Global platform registry (read-only, for admin UI dropdown) ─

class PlatformRegistryItem(BaseModel):
    slug: str
    display_name: str
    base_url: str
    profile_url_template: str


# ── Student Platform Profiles ──────────────────────────────

class StudentProfileEntry(BaseModel):
    """One platform link for a student."""
    platform_slug: str
    username: str
    linked_at: Optional[datetime] = None
    verified: bool = False


class LinkPlatformRequest(BaseModel):
    """Student links one or more platform usernames at once."""
    university_id: str
    student_id: str
    profiles: List[StudentProfileEntry]


class StudentPlatformProfileOut(BaseModel):
    university_id: str
    student_id: str
    profiles: List[StudentProfileEntry]


# ── Bulk link via CSV / JSON ────────────────────────────────

class BulkLinkRow(BaseModel):
    """One row in a bulk-link upload: maps student → platform username."""
    student_id: str
    platform_slug: str
    username: str


class BulkLinkRequest(BaseModel):
    """Admin uploads a batch of student ↔ platform links."""
    university_id: str
    rows: List[BulkLinkRow] = Field(..., max_length=10_000)


class BulkLinkResponse(BaseModel):
    total: int
    linked: int
    skipped: int
    errors: List[str] = []
