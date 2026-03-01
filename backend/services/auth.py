"""
Authentication service — signup, login, password verification, JWT tokens.

Three MongoDB collections store users by role:
  - users_students
  - users_teachers
  - users_admins

Each document stores hashed passwords (bcrypt) — never plaintext.
"""

from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Optional

from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import jwt, JWTError

from backend.clients.mongo_client import get_db
from backend.schemas.auth import (
    SignupRequest, SignupResponse,
    LoginRequest, LoginResponse, UserProfile,
)


# ── Password hashing ───────────────────────────────────────

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── JWT tokens ──────────────────────────────────────────────

JWT_SECRET = "scholar-pulse-super-secret-key-change-in-prod"   # move to .env for production
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# ── Collection routing by role ──────────────────────────────

ROLE_COLLECTIONS = {
    "student": "users_students",
    "teacher": "users_teachers",
    "admin": "users_admins",
}


def _col(role: str):
    db = get_db()
    col_name = ROLE_COLLECTIONS.get(role)
    if not col_name:
        raise HTTPException(status_code=400, detail=f"Unknown role: {role}")
    return db[col_name]


# ── Signup ──────────────────────────────────────────────────

async def signup_user(req: SignupRequest) -> SignupResponse:
    col = _col(req.role)

    # Check duplicate email
    existing = await col.find_one({"email": req.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user_id = str(uuid4())
    now = datetime.now(timezone.utc)

    doc = {
        "user_id": user_id,
        "name": req.name,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "role": req.role,
        "university_id": req.university_id,
        "department": req.department,
        "batch": req.batch,
        "section": req.section,
        "created_at": now,
        "updated_at": now,
    }

    await col.insert_one(doc)
    return SignupResponse(
        message="Account created successfully",
        user_id=user_id,
        role=req.role,
        name=req.name,
    )


# ── Login ───────────────────────────────────────────────────

async def login_user(req: LoginRequest) -> LoginResponse:
    """
    Searches all three role collections for matching email,
    verifies the password hash, and returns a JWT.
    """
    user_doc = None
    matched_role = None

    for role, col_name in ROLE_COLLECTIONS.items():
        db = get_db()
        doc = await db[col_name].find_one({"email": req.email})
        if doc:
            user_doc = doc
            matched_role = role
            break

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email",
        )

    if not verify_password(req.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    # Build JWT
    token = create_access_token({
        "sub": user_doc["user_id"],
        "role": matched_role,
        "email": user_doc["email"],
        "university_id": user_doc.get("university_id", "UNI001"),
    })

    user_profile = UserProfile(
        id=user_doc["user_id"],
        name=user_doc["name"],
        email=user_doc["email"],
        role=matched_role,
        university_id=user_doc.get("university_id", "UNI001"),
        department=user_doc.get("department"),
        batch=user_doc.get("batch"),
        created_at=user_doc.get("created_at"),
    )

    return LoginResponse(access_token=token, user=user_profile)


# ── Auth middleware ─────────────────────────────────────────
# Supports BOTH:
#   1. JWT Bearer token  (new — real auth)
#   2. X-Actor-Id / X-Actor-Role headers  (old — backward compat during dev)

async def get_current_actor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_actor_id: Optional[str] = Header(None),
    x_actor_role: Optional[str] = Header(None),
):
    # Try JWT first
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        return {
            "id": payload["sub"],
            "role": payload["role"],
            "email": payload.get("email"),
            "university_id": payload.get("university_id", "UNI001"),
        }

    # Fallback to header-based auth (for Swagger / dev testing)
    if x_actor_id and x_actor_role:
        if x_actor_role not in {"student", "teacher", "admin"}:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role")
        return {"id": x_actor_id, "role": x_actor_role, "university_id": "UNI001"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide a Bearer token or X-Actor-Id + X-Actor-Role headers",
    )

