"""app/api/routes/progress.py — Career Readiness Score + Progress endpoints."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.models import CareerScore, QuizResult, Resume, InterviewSession
from app.models.user import User
from app.services.report_service import generate_career_report_pdf

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("/report", summary="Download the Career Readiness Report as a PDF")
async def download_report(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    import io
    pdf_bytes = await generate_career_report_pdf(str(current_user.id), db)
    safe_name = (current_user.name or "user").replace(" ", "_")
    filename = f"Career_Report_{safe_name}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/score", summary="Get current Career Readiness Score")
async def get_career_score(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    uid = current_user.id

    # Latest resume score
    r_res = await db.execute(
        select(Resume).where(Resume.user_id == uid, Resume.ats_score != None)
        .order_by(desc(Resume.analyzed_at)).limit(1)
    )
    resume = r_res.scalar_one_or_none()
    resume_score = resume.ats_score if resume else 0

    # Average quiz score (last 5)
    q_res = await db.execute(
        select(QuizResult).where(QuizResult.user_id == uid, QuizResult.score != None)
        .order_by(desc(QuizResult.taken_at)).limit(5)
    )
    quizzes = q_res.scalars().all()
    quiz_score = int(sum(q.score for q in quizzes) / len(quizzes)) if quizzes else 0

    # Latest interview score
    i_res = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == uid, InterviewSession.readiness_score != None)
        .order_by(desc(InterviewSession.created_at)).limit(1)
    )
    interview = i_res.scalar_one_or_none()
    interview_score = interview.readiness_score if interview else 0

    # Skill score — derived from readiness % in latest skill gap (stored in CareerScore)
    skill_score = 0
    cs_res = await db.execute(
        select(CareerScore).where(CareerScore.user_id == uid)
        .order_by(desc(CareerScore.computed_at)).limit(1)
    )
    prev_score = cs_res.scalar_one_or_none()
    if prev_score:
        skill_score = prev_score.skill_score or 0

    # Weighted overall
    overall = int(
        resume_score    * 0.30 +
        skill_score     * 0.25 +
        quiz_score      * 0.25 +
        interview_score * 0.20
    )

    # Recommendations
    recommendations = []
    if resume_score < 70:
        recommendations.append("Improve your resume ATS score — upload an updated resume")
    if skill_score < 60:
        recommendations.append("Run a skill gap analysis to identify what to learn next")
    if quiz_score < 70:
        recommendations.append("Practice more quizzes to strengthen weak topic areas")
    if interview_score < 60:
        recommendations.append("Complete a mock interview session to build confidence")

    # Persist snapshot
    snapshot = CareerScore(
        user_id=uid,
        resume_score=resume_score,
        skill_score=skill_score,
        interview_score=interview_score,
        quiz_score=quiz_score,
        overall_score=overall,
        recommendations=recommendations,
    )
    db.add(snapshot)
    await db.commit()

    return {
        "overall_score":     overall,
        "components": {
            "resume_score":    resume_score,
            "skill_score":     skill_score,
            "interview_score": interview_score,
            "quiz_score":      quiz_score,
        },
        "recommendations":   recommendations,
        "computed_at":       datetime.now(timezone.utc).isoformat(),
    }


@router.get("/history", summary="Score history for trend chart")
async def get_score_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CareerScore).where(CareerScore.user_id == current_user.id)
        .order_by(CareerScore.computed_at).limit(30)
    )
    scores = result.scalars().all()
    return [
        {
            "overall_score": s.overall_score,
            "resume_score":  s.resume_score,
            "skill_score":   s.skill_score,
            "quiz_score":    s.quiz_score,
            "computed_at":   s.computed_at.isoformat(),
        }
        for s in scores
    ]
