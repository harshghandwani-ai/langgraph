"""
auth_utils.py — JWT token creation and FastAPI dependency for current user.

Usage:
    from auth_utils import get_current_user, create_access_token

    # In a route:
    @router.get("/me")
    async def me(user = Depends(get_current_user)):
        return {"user_id": user.id, "username": user.username}
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS

# ── Bearer token extractor ────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


# ── Token payload model ───────────────────────────────────────────────────────

class TokenData(BaseModel):
    user_id: int
    username: str
    email: str


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(user_id: int, username: str, email: str) -> str:
    """Return a signed JWT that expires in JWT_EXPIRE_DAYS days."""
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> TokenData:
    """
    Validate the Bearer token and return the decoded user data.
    Raises HTTP 401 if token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
        username: str = payload["username"]
        email: str = payload["email"]
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenData(user_id=user_id, username=username, email=email)
