"""Auth router — signup + login endpoints (no auth required)."""

from fastapi import APIRouter
from backend.schemas.auth import (
    SignupRequest, SignupResponse,
    LoginRequest, LoginResponse,
)
from backend.services.auth import signup_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse)
async def signup(req: SignupRequest):
    """Create a new student / teacher / admin account."""
    return await signup_user(req)


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Verify email + password, return JWT token."""
    return await login_user(req)
