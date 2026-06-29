"""
app/api/routes/auth.py
───────────────────────
Authentication endpoints: register, login, refresh, /me, logout.

All password handling happens in app/core/security.py.
This file only handles HTTP: request parsing, DB queries, response shaping.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.db.database import get_db
from app.models.models import UserSession
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    RefreshTokenRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Register ───────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(
    body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    # Check for existing email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        target_role=body.target_role,
    )
    db.add(user)
    await db.flush()        # flush to get user.id before creating session

    # Create login session (flush first to get session.id for token payload)
    session = UserSession(user_id=user.id)
    db.add(session)
    await db.flush()

    # BUG-04 FIX: generate tokens now so we can hash the refresh token
    token_data = {"sub": str(user.id), "email": user.email, "session_id": str(session.id)}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store hashed refresh token so we can verify it during rotation
    session.refresh_token_hash = hash_password(refresh_token)

    await db.commit()
    await db.refresh(user)

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
    return AuthResponse(user=UserResponse.model_validate(user), tokens=token_response)


# ── Login ──────────────────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login and receive JWT tokens",
)
async def login(
    body: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    # Look up user
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Use same error for both "user not found" and "wrong password"
    # to prevent email enumeration attacks
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )

    if user is None or not verify_password(body.password, user.hashed_password):
        raise auth_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    # Create a new session for this login (flush to get session.id for token payload)
    session = UserSession(user_id=user.id)
    db.add(session)
    await db.flush()

    # BUG-04 FIX: generate tokens now so we can hash the refresh token
    token_data = {"sub": str(user.id), "email": user.email, "session_id": str(session.id)}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store hashed refresh token for secure rotation / revocation
    session.refresh_token_hash = hash_password(refresh_token)

    await db.commit()
    await db.refresh(session)

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
    return AuthResponse(user=UserResponse.model_validate(user), tokens=token_response)


# ── Refresh Token ──────────────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange refresh token for a new access token",
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = verify_token(body.refresh_token, expected_type="refresh")
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["session_id"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    # Verify session still exists
    session_result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found. Please login again.",
        )

    # BUG-04 FIX: verify the submitted refresh token against the stored bcrypt hash.
    # This means stolen JWTs that were never issued by us are rejected even if
    # the signature is technically valid (e.g. after a secret rotation edge case).
    if not session.refresh_token_hash or not verify_password(
        body.refresh_token, session.refresh_token_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token does not match session. Please login again.",
        )

    # Load user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    # BUG-02 FIX: build and return TokenResponse directly — never go through
    # _generate_tokens() (which returns AuthResponse) for this endpoint.
    token_data = {"sub": str(user.id), "email": user.email, "session_id": str(session.id)}
    new_access_token  = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Rotate the stored hash so each refresh token is single-use
    session.refresh_token_hash = hash_password(new_refresh_token)
    await db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


# ── Get Current User ───────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user's profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


# ── Update Profile ─────────────────────────────────────────────────────────────
@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update the current user's profile",
)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if body.name is not None:
        current_user.name = body.name
    if body.target_role is not None:
        current_user.target_role = body.target_role
    if body.current_skills is not None:
        current_user.current_skills = body.current_skills

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


# ── Logout ─────────────────────────────────────────────────────────────────────
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate the current session",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    # Delete all sessions for this user (logout from all devices)
    # For "logout from this device only", you'd need to pass the session_id
    from sqlalchemy import delete
    await db.execute(
        delete(UserSession).where(UserSession.user_id == current_user.id)
    )
    await db.commit()


