"""
routers/auth.py — Real JWT authentication endpoints.

Endpoints:
  POST /api/auth/register  — create account, return JWT
  POST /api/auth/login     — sign in, return JWT
  GET  /api/auth/me        — return current user info (requires token)
"""
from fastapi import APIRouter, Depends, HTTPException, status
import bcrypt
from pydantic import BaseModel

from auth_utils import TokenData, create_access_token, get_current_user
from db import get_user_by_email, insert_user

router = APIRouter()

# ── Password hashing ──────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    """Hash password using bcrypt."""
    pw_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest) -> TokenResponse:
    """Create a new account. Returns a JWT on success."""
    if not body.username.strip():
        raise HTTPException(status_code=422, detail="Username cannot be empty.")
    if not body.email.strip():
        raise HTTPException(status_code=422, detail="Email cannot be empty.")
    if len(body.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters.")

    # Check duplicate email
    if get_user_by_email(body.email.strip()):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    hashed = _hash_password(body.password)
    try:
        user_id = insert_user(
            username=body.username.strip(),
            email=body.email.strip(),
            password_hash=hashed,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not create account: {exc}") from exc

    token = create_access_token(
        user_id=user_id,
        username=body.username.strip(),
        email=body.email.strip(),
    )
    return TokenResponse(
        token=token,
        user=UserResponse(username=body.username.strip(), email=body.email.strip()),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Verify credentials and return a JWT."""
    if not body.email.strip() or not body.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email and password are required.",
        )

    user = get_user_by_email(body.email.strip())
    if not user or not _verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
    )
    return TokenResponse(
        token=token,
        user=UserResponse(username=user["username"], email=user["email"]),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: TokenData = Depends(get_current_user)) -> UserResponse:
    """Return the current authenticated user's info."""
    return UserResponse(username=current_user.username, email=current_user.email)
