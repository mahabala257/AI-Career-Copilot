"""
app/services/user_context.py
─────────────────────────────
Loads a user's most recent agent context (resume analysis, profile skills,
quiz weak areas) directly from PostgreSQL and shapes it into the
CareerCopilotState fields that downstream agents read.

Why this exists
───────────────
Dedicated endpoints use a unique per-request LangGraph thread_id (to avoid
cross-request state bleed and save tokens), which means an agent can no longer
"remember" a prior Resume/Skill-Gap run via the checkpointer. Instead of
relying on conversation memory, we load the latest persisted results from the
database and inject them explicitly. This is deterministic and works every
time — even after a restart — so e.g. the Project Recommender's portfolio
score reflects the user's real resume + skills.
"""
import logging
import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import QuizResult, Resume
from app.models.user import User

logger = logging.getLogger(__name__)


async def load_user_agent_context(user_id: str, db: AsyncSession) -> dict:
    """
    Return a dict with the agent-state fields that benefit from prior results:
      resume_analysis     — latest analysed resume (extracted_skills, raw_text, ...)
      skill_gap_analysis  — light gap derived from the resume's missing_skills
      quiz_output         — latest quiz weak areas (for the study planner)
      current_skills      — resume skills merged with profile skills

    Every field degrades to empty/{} when the user has no prior data, so callers
    can inject unconditionally.
    """
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        return {"resume_analysis": {}, "skill_gap_analysis": {}, "quiz_output": {}, "current_skills": []}

    # ── Latest analysed resume ─────────────────────────────────────────────────
    resume = (
        await db.execute(
            select(Resume)
            .where(Resume.user_id == uid, Resume.ats_score.isnot(None))
            .order_by(desc(Resume.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    # ── Profile skills ─────────────────────────────────────────────────────────
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    profile_skills = list(user.current_skills) if (user and user.current_skills) else []

    resume_analysis: dict = {}
    skill_gap_analysis: dict = {}
    if resume:
        resume_analysis = {
            "ats_score":        resume.ats_score or 0,
            "extracted_skills": list(resume.extracted_skills or []),
            "missing_skills":   list(resume.missing_skills or []),
            "strengths":        list(resume.strengths or []),
            "suggestions":      list(resume.suggestions or []),
            "raw_text":         resume.raw_text or "",
        }
        if resume.missing_skills:
            skill_gap_analysis = {
                "priority_order": list(resume.missing_skills),
                "missing_skills": list(resume.missing_skills),
            }

    # Merge resume-extracted skills with profile skills (deduped, order-preserving)
    merged_skills = list(dict.fromkeys(
        (resume_analysis.get("extracted_skills") or []) + profile_skills
    ))
    if merged_skills:
        resume_analysis.setdefault("extracted_skills", [])
        resume_analysis["extracted_skills"] = merged_skills

    # ── Latest quiz weak areas ─────────────────────────────────────────────────
    quiz = (
        await db.execute(
            select(QuizResult)
            .where(QuizResult.user_id == uid, QuizResult.weak_areas.isnot(None))
            .order_by(desc(QuizResult.taken_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    quiz_output = {"weak_areas": list(quiz.weak_areas)} if (quiz and quiz.weak_areas) else {}

    logger.info(
        f"[UserContext] user={user_id} | resume={'yes' if resume else 'no'} | "
        f"skills={len(merged_skills)} | quiz_weak={len(quiz_output.get('weak_areas', []))}"
    )

    return {
        "resume_analysis":    resume_analysis,
        "skill_gap_analysis": skill_gap_analysis,
        "quiz_output":        quiz_output,
        "current_skills":     merged_skills,
    }
