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

from app.agents.graph import career_copilot_graph
from app.agents.state import create_initial_state

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
    # Inject extras that placeholders don't have
    initial_state["current_skills"]         = current_skills  # type: ignore[index]
    initial_state["generate_learning_path"] = generate_learning_path  # type: ignore[index]
    initial_state["generate_roadmap"]       = generate_roadmap  # type: ignore[index]
    initial_state["available_hours"]        = available_hours  # type: ignore[index]

    logger.info(f"[SkillGapService] Invoking LangGraph | user={user_id} | role={target_role}")

    result = await career_copilot_graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": session_id}},
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

    return {
        "analysis":    analysis,
        "agent_error": error,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


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
