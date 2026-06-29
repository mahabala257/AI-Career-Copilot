"""
app/services/skill_gap_service.py
───────────────────────────────────
Business logic layer for skill gap analysis.
Orchestrates: LangGraph invocation → optional DB persistence → response shaping.
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_graph
from app.agents.state import AgentName, create_initial_state

logger = logging.getLogger(__name__)


async def run_skill_gap_analysis(
    *,
    user_id: str,
    session_id: str,
    target_role: str,
    current_skills: list[str],
    generate_learning_path: bool = False,
    generate_roadmap: bool = False,
    available_hours: float = 2.0,
    db: AsyncSession,
) -> dict:
    """
    Run skill gap analysis via LangGraph.
    If the user has a recent resume analysis in the session, the agent
    automatically reads extracted_skills from it (via shared state).
    """
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Analyze my skill gaps for the role: {target_role}",
        target_role=target_role,
    )
    # Inject skill gap inputs (now declared in CareerCopilotState)
    initial_state["current_skills"]         = current_skills  # type: ignore[index]
    initial_state["generate_learning_path"] = generate_learning_path  # type: ignore[index]
    initial_state["generate_roadmap"]       = generate_roadmap  # type: ignore[index]
    initial_state["available_hours"]        = available_hours  # type: ignore[index]
    # Skip supervisor LLM call — we know exactly which agent to run
    initial_state["next_agent"]             = AgentName.SKILL_GAP  # type: ignore[index]
    initial_state["agent_queue"]            = []  # type: ignore[index]

    logger.info(f"[SkillGapService] Invoking LangGraph | user={user_id} | role={target_role}")

    result = await get_graph().ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )

    analysis  = result.get("skill_gap_analysis", {})
    error     = result.get("error")

    # Persist updated skills to user profile
    if analysis.get("current_skills"):
        await _update_user_skills(
            user_id=user_id,
            target_role=target_role,
            skills=analysis["current_skills"],
            db=db,
        )

    # Persist the readiness % so the dashboard's Skills score reflects it.
    readiness = analysis.get("overall_readiness_percent")
    if isinstance(readiness, (int, float)) and readiness > 0:
        await _save_skill_readiness(user_id=user_id, readiness=int(readiness), db=db)

    return {
        "analysis":    analysis,
        "agent_error": error,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


async def _save_skill_readiness(user_id: str, readiness: int, db: AsyncSession) -> None:
    """
    Write a CareerScore snapshot carrying the new skill readiness so the
    dashboard (which reads skill_score from the latest CareerScore row) reflects
    it. Other components are carried over from the latest snapshot and the
    overall score is recomputed with the standard weights.
    """
    try:
        from sqlalchemy import desc, select
        from app.models.models import CareerScore

        latest = (await db.execute(
            select(CareerScore).where(CareerScore.user_id == uuid.UUID(user_id))
            .order_by(desc(CareerScore.computed_at)).limit(1)
        )).scalar_one_or_none()

        resume_s    = (latest.resume_score    if latest else 0) or 0
        quiz_s      = (latest.quiz_score      if latest else 0) or 0
        interview_s = (latest.interview_score if latest else 0) or 0
        overall = int(resume_s * 0.30 + readiness * 0.25 + quiz_s * 0.25 + interview_s * 0.20)

        db.add(CareerScore(
            user_id=uuid.UUID(user_id),
            resume_score=resume_s, skill_score=readiness,
            quiz_score=quiz_s, interview_score=interview_s,
            overall_score=overall,
            recommendations=(latest.recommendations if latest else []) or [],
        ))
        await db.commit()
        logger.info(f"[SkillGapService] Saved skill readiness={readiness} | user={user_id}")
    except Exception as e:
        logger.error(f"[SkillGapService] Failed to save skill readiness: {e}")


async def _update_user_skills(
    user_id: str,
    target_role: str,
    skills: list[str],
    db: AsyncSession,
) -> None:
    """Persist target_role and current_skills back to the user profile."""
    try:
        from sqlalchemy import select
        from app.models.user import User
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user:
            user.target_role    = target_role
            user.current_skills = skills
            await db.commit()
            logger.info(f"[SkillGapService] Updated user profile | user={user_id}")
    except Exception as e:
        logger.error(f"[SkillGapService] Failed to update user: {e}")
