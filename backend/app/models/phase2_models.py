"""
app/models/phase2_models.py
────────────────────────────
SQLAlchemy ORM models for Phase 2 agents.

Tables:
  linkedin_optimizations  — LinkedIn Optimization Agent results
  project_recommendations — Project Recommendation Agent results
  english_evaluations     — Spoken English Agent evaluation results
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class LinkedInOptimization(Base):
    """
    Stores each LinkedIn profile optimization run.
    One user can run multiple optimizations over time to track improvement.
    """
    __tablename__ = "linkedin_optimizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Raw input the user submitted
    original_headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_about: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_skills: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Scores
    current_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    optimized_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full agent output (all rewritten sections, keyword analysis, etc.)
    optimization_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="linkedin_optimizations")  # type: ignore[name-defined]


class ProjectRecommendation(Base):
    """
    Stores project recommendation sessions.
    Each run produces a ranked list of projects tailored to the user's
    target role, skill gaps, and experience level.
    """
    __tablename__ = "project_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    time_available_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full agent output: list of recommended projects with full details
    recommendations_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    portfolio_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="project_recommendations")  # type: ignore[name-defined]


class EnglishEvaluation(Base):
    """
    Stores each Spoken English evaluation.
    Users can track improvement in grammar, fluency, and structure over time.
    The practice_scripts field holds personalised scripts generated per session.
    """
    __tablename__ = "english_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # The text the user submitted
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Context: what was the user doing? Interview answer? Email? Self-intro?
    context_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    question_answered: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Aggregate score (0-100)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Breakdown: grammar, fluency, structure, vocabulary, conciseness
    scores_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # List of issues with type, found text, and suggestion
    issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # STAR format compliance analysis
    star_compliance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Personalised practice scripts (elevator pitch, self intro, HR answers)
    practice_scripts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Vocabulary upgrade suggestions
    vocabulary_upgrades: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="english_evaluations")  # type: ignore[name-defined]
