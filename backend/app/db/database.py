"""
app/db/database.py
──────────────────
SQLAlchemy async engine setup.

Why async?
  FastAPI is async-first. Using sync SQLAlchemy would block the event loop
  on every DB query, destroying concurrent request performance.
  asyncpg + SQLAlchemy async = true non-blocking I/O.

Three exports that the rest of the app uses:
  - engine       → used by Alembic and startup checks
  - AsyncSession → used in route dependencies via get_db()
  - Base         → all ORM models inherit from this
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────────
# pool_pre_ping=True: tests each connection before use — handles Render's
#   PostgreSQL which drops idle connections after a period.
# pool_size / max_overflow: tuned for a single Render free-tier instance.
#   Scale up these values when moving to paid tier.
# echo=True in development shows all SQL statements in terminal — very helpful
#   for debugging ORM queries. Off in production.
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.is_development,
)

# ── Session Factory ────────────────────────────────────────────────────────────
# expire_on_commit=False prevents SQLAlchemy from expiring ORM objects after
# a commit, which would cause lazy-load errors in async context (since there's
# no active session at that point). With async, always keep this False.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Declarative Base ───────────────────────────────────────────────────────────
# All ORM models (User, Resume, QuizResult, etc.) inherit from Base.
# Base.metadata holds the schema — Alembic uses this to auto-generate migrations.
class Base(DeclarativeBase):
    pass


# ── Dependency: get_db ────────────────────────────────────────────────────────
# Used in FastAPI route dependencies: db: AsyncSession = Depends(get_db)
# The try/finally guarantees the session is always closed, even on exceptions.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Health check helper ────────────────────────────────────────────────────────
# Called during FastAPI startup to verify DB connection before accepting traffic.
async def check_db_connection() -> bool:
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Connection check failed: {e}")
        return False
