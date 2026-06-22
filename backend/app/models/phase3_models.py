"""
app/models/phase3_models.py
────────────────────────────
SQLAlchemy ORM models for Phase 3 agents.

Tables:
  company_researches      — Company Research Agent results
  internship_researches   — Internship Research Agent results
  wellness_checkins       — Wellness & Motivation Agent sessions
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CompanyResearch(Base):
    """
    Stores each company research session.
    One user can research multiple companies; each run is persisted.
    The full agent output (tech stack, interview style, prep strategy) lives in research_data.
    """
    __tablename__ = "company_researches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_role:  Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Skill alignment score (0-100) — how well the user's skills match this company's needs
    alignment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full agent output
    research_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="company_researches"
    )


class InternshipResearch(Base):
    """
    Stores internship research sessions.
    Captures the student's education context and the full
    recommended company list + application timeline.
    """
    __tablename__ = "internship_researches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_role:     Mapped[str | None] = mapped_column(String(100), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(50),  nullable=True)
    college_tier:    Mapped[str | None] = mapped_column(String(20),  nullable=True)
    available_from:  Mapped[str | None] = mapped_column(String(30),  nullable=True)

    # Full agent output
    research_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="internship_researches"
    )


class WellnessCheckin(Base):
    """
    Stores each Wellness & Motivation check-in.
    The professional_help_flag is set when the agent detects
    signals that warrant suggesting professional mental health support.
    """
    __tablename__ = "wellness_checkins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # The user's free-text message
    mood_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Burnout risk level: "low" | "medium" | "high"
    burnout_risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Full agent response
    response_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Set to True when the agent detects serious mental health signals
    professional_help_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="wellness_checkins"
    )
