"""Schemas for user authentication — signup, login, token responses."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


# ── Signup ──────────────────────────────────────────────────

class SignupRequest(BaseModel):
    """New user registration."""
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(..., pattern="^(student|teacher|admin)$")
    university_id: str = Field(default="UNI001")
    # Optional fields for students
    department: Optional[str] = None
    batch: Optional[str] = None
    section: Optional[str] = None


class SignupResponse(BaseModel):
    message: str
    user_id: str
    role: str
    name: str


# ── Login ───────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserProfile"


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    university_id: str
    department: Optional[str] = None
    batch: Optional[str] = None
    created_at: Optional[datetime] = None


# Fix forward reference
LoginResponse.model_rebuild()
