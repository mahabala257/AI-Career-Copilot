"""
app/api/routes/notifications.py — computed notification feed.

Notifications are derived on the fly from the user's current state (no table):
nudges for unfinished steps, progress acknowledgements, and tips. The frontend
tracks "dismissed" ids in localStorage, so this stays stateless and simple.
"""
import logging
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.models import CareerScore, InterviewSession, QuizResult, Resume, StudyPlan
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class Notification(BaseModel):
    id:       str            # stable id so the client can mark it read/dismissed
    title:    str
    body:     str
    severity: str            # "info" | "success" | "warning" | "action"
    action:   str | None = None   # frontend route to navigate to


async def _count(db: AsyncSession, model, user_id) -> int:
    return (await db.execute(
        select(func.count()).select_from(model).where(model.user_id == user_id)
    )).scalar() or 0


@router.get("", response_model=list[Notification], summary="Get the user's notification feed")
async def get_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[Notification]:
    uid = current_user.id
    notes: list[Notification] = []

    # Profile / target role
    if not current_user.target_role:
        notes.append(Notification(
            id="set-role", title="Set your target role",
            body="Add a target role in your Profile so every tool can personalise for you.",
            severity="action", action="/profile",
        ))

    # Resume
    resume = (await db.execute(
        select(Resume).where(Resume.user_id == uid, Resume.ats_score.isnot(None))
        .order_by(desc(Resume.created_at)).limit(1)
    )).scalar_one_or_none()
    if not resume:
        notes.append(Notification(
            id="upload-resume", title="Upload your resume",
            body="Get your ATS score and see which skills you're missing.",
            severity="action", action="/resume",
        ))
    else:
        if (resume.ats_score or 0) >= 75:
            notes.append(Notification(
                id="ats-strong", title=f"Strong resume — ATS {resume.ats_score}/100 ✅",
                body="Nice! Now optimise your LinkedIn to match.",
                severity="success", action="/linkedin",
            ))
        else:
            notes.append(Notification(
                id="ats-improve", title=f"Resume ATS: {resume.ats_score}/100",
                body="A few tweaks can raise this. Check the suggestions in Resume Analyzer.",
                severity="warning", action="/resume",
            ))

    # Quizzes
    quiz_count = await _count(db, QuizResult, uid)
    if quiz_count == 0:
        notes.append(Notification(
            id="first-quiz", title="Take your first quiz",
            body="Practice MCQs to find your weak areas — even 10 minutes helps.",
            severity="action", action="/quiz",
        ))

    # Interviews
    interview_count = await _count(db, InterviewSession, uid)
    if interview_count == 0:
        notes.append(Notification(
            id="first-interview", title="Try a mock interview",
            body="Generate role-specific questions and get your answers evaluated.",
            severity="action", action="/interview",
        ))

    # Study plan
    plan = (await db.execute(
        select(StudyPlan).where(StudyPlan.user_id == uid, StudyPlan.is_active == True).limit(1)
    )).scalar_one_or_none()
    if not plan:
        notes.append(Notification(
            id="make-plan", title="Create a study plan",
            body="Turn your skill gaps into a daily/weekly plan you can follow.",
            severity="action", action="/planner",
        ))

    # Overall score acknowledgement
    score = (await db.execute(
        select(CareerScore).where(CareerScore.user_id == uid)
        .order_by(desc(CareerScore.computed_at)).limit(1)
    )).scalar_one_or_none()
    if score and score.overall_score is not None:
        notes.append(Notification(
            id="career-score", title=f"Career readiness: {score.overall_score}/100",
            body="Download your full report from the dashboard to see the breakdown.",
            severity="info",
        ))

    # Always: introduce the assistant
    notes.append(Notification(
        id="try-assistant", title="Meet your AI Assistant 🤖",
        body="Ask anything about your career in one chat — it routes to the right specialist.",
        severity="info", action="/chat",
    ))

    return notes
