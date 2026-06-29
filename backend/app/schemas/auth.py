"""
app/schemas/auth.py
────────────────────
Pydantic schemas for authentication endpoints.

Why separate schemas from ORM models?
  - ORM models are DB representations — they have hashed_password, internal IDs, etc.
  - Schemas are API contracts — they control what clients send and receive.
  - Keeping them separate prevents accidentally exposing hashed_password in responses.
  - Also allows the API shape to change independently of the DB shape.

Naming convention:
  UserCreate  → POST body for creating a resource
  UserResponse → what the API returns (never includes sensitive fields)
  TokenResponse → what login returns
"""

import uuid

from pydantic import BaseModel, EmailStr, field_validator


# ── Register ───────────────────────────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr            # pydantic validates email format automatically
    password: str
    target_role: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


# ── Login ──────────────────────────────────────────────────────────────────────
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Token responses ────────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int            # seconds until access token expires


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── User in responses ──────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    target_role: str | None
    current_skills: list | None
    is_active: bool

    # model_config tells Pydantic to read data from ORM object attributes,
    # not just dict keys. Required when returning SQLAlchemy model instances.
    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Returned by both register and login."""
    user: UserResponse
    tokens: TokenResponse


# ── Update profile ─────────────────────────────────────────────────────────────
class UpdateProfileRequest(BaseModel):
    name: str | None = None
    target_role: str | None = None
    current_skills: list[str] | None = None
