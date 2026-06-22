"""
app/core/security.py
─────────────────────
All authentication logic lives here — password hashing and JWT handling.
This is kept separate from routes so it can be tested in isolation
and reused across different endpoints.

JWT flow:
  1. User logs in → create_access_token() + create_refresh_token()
  2. User sends access token in Authorization: Bearer <token>
  3. verify_token() decodes it → returns the payload (user_id + email)
  4. Access token expires in 30 min → frontend uses refresh token to get new one
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ── Password Hashing ───────────────────────────────────────────────────────────
# bcrypt is the industry standard for password hashing.
# deprecated="auto" means passlib will automatically upgrade old hashes
# when users log in (future-proofing if you add argon2 later).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password. Store the result, never the plain text."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a submitted password against a stored hash.
    Uses constant-time comparison internally (bcrypt) — safe against timing attacks.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ─────────────────────────────────────────────────────────────────
def create_access_token(data: dict[str, Any]) -> str:
    """
    Create a short-lived JWT access token.
    
    'data' should contain at minimum:
      { "sub": str(user.id), "email": user.email }
    
    The 'sub' (subject) claim is the JWT standard field for user identity.
    We use the user UUID so even if email changes, tokens stay valid.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create a long-lived JWT refresh token.
    Stored as a hash in the database (UserSession.refresh_token_hash)
    so we can invalidate it on logout without a token blacklist.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Raises ValueError on:
      - Expired tokens
      - Invalid signature
      - Wrong token type (access vs refresh)
      - Malformed tokens
    
    Returns the full decoded payload on success.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != expected_type:
            raise ValueError(f"Expected {expected_type} token, got {payload.get('type')}")
        if payload.get("sub") is None:
            raise ValueError("Token missing 'sub' claim")
        return payload
    except JWTError as e:
        raise ValueError(f"Token validation failed: {e}") from e
