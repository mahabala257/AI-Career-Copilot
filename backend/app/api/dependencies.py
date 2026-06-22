"""
app/api/dependencies.py
────────────────────────
FastAPI dependency injection functions.

These are used in route signatures like:
    current_user: User = Depends(get_current_user)
    db: AsyncSession = Depends(get_db)

FastAPI calls them automatically before executing the route handler,
passing the result as the parameter. This keeps auth logic out of routes.

Dependency chain for protected routes:
    Request arrives
        → oauth2_scheme extracts Bearer token from Authorization header
        → get_current_user() verifies token
        → get_current_active_user() checks user.is_active
        → route handler receives verified User object
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import verify_token
from app.db.database import get_db
from app.models.user import User

# ── OAuth2 scheme ──────────────────────────────────────────────────────────────
# tokenUrl tells Swagger UI where to send login requests for the "Authorize" button.
# auto_error=True means FastAPI returns 401 automatically if no token is present,
# before our code even runs.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=True,
)

# An optional version that doesn't raise 401 for public endpoints
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT, then load the User from the database.
    
    Why load from DB instead of trusting only the JWT?
      - Lets us invalidate users (deactivate account) without waiting for token expiry
      - Gives us the full, up-to-date User object (not a stale token snapshot)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token, expected_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Load user from DB
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Check that the authenticated user's account is active.
    Deactivating a user (is_active=False) immediately blocks all their requests
    even with a valid token — no need to wait for token expiry.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support.",
        )
    return current_user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Returns the authenticated User or None for public endpoints
    that behave differently when a user is logged in.
    """
    if token is None:
        return None
    try:
        payload = verify_token(token, expected_type="access")
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        return result.scalar_one_or_none()
    except (ValueError, Exception):
        return None
