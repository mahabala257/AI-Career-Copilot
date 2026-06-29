"""
app/models/__init__.py
───────────────────────
Import all ORM models here so SQLAlchemy's Base.metadata registers every table.
This file must import ALL models — missing an import means Alembic won't see
the table and may try to DROP it when running autogenerate.
"""
from app.models.user import User
from app.models.models import (
    UserSession,
    Resume,
    QuizResult,
    InterviewSession,
    CareerScore,
    StudyPlan,
)
from app.models.phase2_models import (
    LinkedInOptimization,
    ProjectRecommendation,
    EnglishEvaluation,
)
from app.models.phase3_models import (
    CompanyResearch,
    InternshipResearch,
    WellnessCheckin,
)

__all__ = [
    "User",
    "UserSession",
    "Resume",
    "QuizResult",
    "InterviewSession",
    "CareerScore",
    "StudyPlan",
    "LinkedInOptimization",
    "ProjectRecommendation",
    "EnglishEvaluation",
    "CompanyResearch",
    "InternshipResearch",
    "WellnessCheckin",
]
