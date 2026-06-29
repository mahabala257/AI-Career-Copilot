"""
app/models/user.py
──────────────────
Users table ORM model.
Every other model has a FK pointing here.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Stored as JSONB array: ["Python", "SQL", "Machine Learning"]
    current_skills: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # back_populates creates bidirectional access:
    #   user.resumes  →  list of Resume objects
    #   resume.user   →  the User object
    resumes: Mapped[list["Resume"]] = relationship(
        "Resume", back_populates="user", cascade="all, delete-orphan"
    )
    quiz_results: Mapped[list["QuizResult"]] = relationship(
        "QuizResult", back_populates="user", cascade="all, delete-orphan"
    )
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="user", cascade="all, delete-orphan"
    )
    career_scores: Mapped[list["CareerScore"]] = relationship(
        "CareerScore", back_populates="user", cascade="all, delete-orphan"
    )
    study_plans: Mapped[list["StudyPlan"]] = relationship(
        "StudyPlan", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    # ── Phase 2 relationships ──────────────────────────────────────────────────
    linkedin_optimizations: Mapped[list["LinkedInOptimization"]] = relationship(  # type: ignore[name-defined]
        "LinkedInOptimization", back_populates="user", cascade="all, delete-orphan"
    )
    project_recommendations: Mapped[list["ProjectRecommendation"]] = relationship(  # type: ignore[name-defined]
        "ProjectRecommendation", back_populates="user", cascade="all, delete-orphan"
    )
    english_evaluations: Mapped[list["EnglishEvaluation"]] = relationship(  # type: ignore[name-defined]
        "EnglishEvaluation", back_populates="user", cascade="all, delete-orphan"
    )

    # ── Phase 3 relationships ──────────────────────────────────────────────────
    company_researches: Mapped[list["CompanyResearch"]] = relationship(  # type: ignore[name-defined]
        "CompanyResearch", back_populates="user", cascade="all, delete-orphan"
    )
    internship_researches: Mapped[list["InternshipResearch"]] = relationship(  # type: ignore[name-defined]
        "InternshipResearch", back_populates="user", cascade="all, delete-orphan"
    )
    wellness_checkins: Mapped[list["WellnessCheckin"]] = relationship(  # type: ignore[name-defined]
        "WellnessCheckin", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
