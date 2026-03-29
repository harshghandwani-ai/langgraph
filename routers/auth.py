"""
routers/auth.py — Authentication endpoints (Phase 1: stub).

Endpoints:
  POST /api/auth/register  — create account (stub, returns mock token)
  POST /api/auth/login     — sign in      (stub, returns mock token)
  GET  /api/auth/me        — current user (stub, reads from token header)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    username: str
    email: str


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


# ── Stub endpoints ─────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest) -> TokenResponse:
    """Phase-1 stub: accepts any credentials and returns a mock token."""
    if not body.username.strip():
        raise HTTPException(status_code=422, detail="Username cannot be empty.")
    if not body.email.strip():
        raise HTTPException(status_code=422, detail="Email cannot be empty.")
    if len(body.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters.")
    return TokenResponse(
        token="stub-token",
        user=UserResponse(username=body.username.strip(), email=body.email.strip()),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Phase-1 stub: accepts any credentials and returns a mock token."""
    if not body.email.strip() or not body.password:
        raise HTTPException(status_code=401, detail="Email and password are required.")
    # Derive a display name from email (part before @)
    username = body.email.split("@")[0]
    return TokenResponse(
        token="stub-token",
        user=UserResponse(username=username, email=body.email.strip()),
    )


@router.get("/me", response_model=UserResponse)
async def me() -> UserResponse:
    """Phase-1 stub: returns a generic current-user object."""
    return UserResponse(username="user", email="user@example.com")
