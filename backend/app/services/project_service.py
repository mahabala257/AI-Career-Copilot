"""
app/services/project_service.py
─────────────────────────────────
Business logic for project recommendations.
Orchestrates: LangGraph invocation → DB persistence → response shaping.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

import uuid
from app.agents.graph import get_graph
from app.agents.state import AgentName, create_initial_state
from app.models.phase2_models import ProjectRecommendation
from app.services.user_context import load_user_agent_context

logger = logging.getLogger(__name__)


async def run_project_recommendations(
    *,
    user_id: str,
    session_id: str,
    target_role: str,
    experience_level: str,
    time_available_weeks: int,
    db: AsyncSession,
) -> dict:
    """
    Invoke Project Recommendation Agent via LangGraph and persist the result.
    The agent reads resume_analysis and skill_gap_analysis from LangGraph
    conversation state automatically if those agents were run in the same session.
    """
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Recommend projects for {target_role} at {experience_level} level",
        target_role=target_role,
        experience_level=experience_level,
        time_available_weeks=time_available_weeks,
    )
    initial_state["next_agent"]  = AgentName.PROJECT_RECOMMEND  # type: ignore[index]
    initial_state["agent_queue"] = []  # type: ignore[index]

    # Inject the user's latest resume + skills so the agent scores the REAL
    # portfolio (replaces the old cross-request LangGraph memory).
    ctx = await load_user_agent_context(user_id, db)
    initial_state["resume_analysis"]    = ctx["resume_analysis"]     # type: ignore[index]
    initial_state["skill_gap_analysis"] = ctx["skill_gap_analysis"]  # type: ignore[index]
    initial_state["current_skills"]     = ctx["current_skills"]      # type: ignore[index]

    logger.info(
        f"[ProjectService] Invoking LangGraph | user={user_id} | "
        f"role={target_role} | level={experience_level}"
    )

    graph  = get_graph()
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )

    recommendations = result.get("project_recommendations_output", {})
    error           = result.get("error")

    # Coerce portfolio_score to int (LLM may return a string) — the DB column is
    # Integer, so a stray string would raise on commit and 500 the request.
    def _to_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    # ── Persist to DB ──────────────────────────────────────────────────────────
    record = ProjectRecommendation(
        user_id=uuid.UUID(user_id),
        target_role=target_role,
        experience_level=experience_level,
        time_available_weeks=time_available_weeks,
        recommendations_data=recommendations,
        portfolio_score=_to_int(recommendations.get("portfolio_score")),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(f"[ProjectService] Persisted | id={record.id} | user={user_id}")

    return {
        "recommendation_id": str(record.id),
        "target_role":       target_role,
        "experience_level":  experience_level,
        "result":            recommendations,
        "agent_error":       error,
        "generated_at":      datetime.now(timezone.utc).isoformat(),
    }


async def get_project_history(user_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the user's past project recommendation runs, most recent first."""
    rows = await db.execute(
        select(ProjectRecommendation)
        .where(ProjectRecommendation.user_id == uuid.UUID(user_id))
        .order_by(desc(ProjectRecommendation.created_at))
        .limit(limit)
    )
    records = rows.scalars().all()
    return [
        {
            "recommendation_id": str(r.id),
            "target_role":       r.target_role,
            "experience_level":  r.experience_level,
            "portfolio_score":   r.portfolio_score,
            "created_at":        r.created_at.isoformat(),
        }
        for r in records
    ]
