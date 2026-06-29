"""
app/services/linkedin_service.py
──────────────────────────────────
Business logic for LinkedIn optimization.
Orchestrates: LangGraph invocation → DB persistence → response shaping.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

import uuid
from app.agents.graph import get_graph
from app.agents.state import AgentName, create_initial_state
from app.core.sanitize import sanitize_user_text
from app.models.phase2_models import LinkedInOptimization
from app.models.user import User

logger = logging.getLogger(__name__)


async def run_linkedin_optimization(
    *,
    user_id: str,
    session_id: str,
    headline: str,
    about: str,
    experience: str,
    skills: list[str],
    target_role: str,
    db: AsyncSession,
) -> dict:
    """
    Invoke the LinkedIn Optimization Agent via LangGraph and persist the result.
    Returns a dict ready for the API response schema.
    """
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Optimize my LinkedIn profile for {target_role}",
        target_role=target_role,
        linkedin_headline=sanitize_user_text(headline, max_len=400),
        linkedin_about=sanitize_user_text(about, max_len=3000),
        linkedin_experience=sanitize_user_text(experience, max_len=5000),
        linkedin_skills=skills,
    )
    initial_state["next_agent"]  = AgentName.LINKEDIN  # type: ignore[index]
    initial_state["agent_queue"] = []  # type: ignore[index]

    logger.info(f"[LinkedInService] Invoking LangGraph | user={user_id} | role={target_role}")

    graph  = get_graph()
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )

    optimization = result.get("linkedin_output", {})
    error        = result.get("error")

    # ── Persist to DB ──────────────────────────────────────────────────────────
    record = LinkedInOptimization(
        user_id=uuid.UUID(user_id),
        original_headline=headline,
        original_about=about,
        original_experience=experience,
        original_skills=skills,
        target_role=target_role,
        current_score=optimization.get("current_score"),
        optimized_score=optimization.get("optimized_score"),
        optimization_data=optimization,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(f"[LinkedInService] Persisted | id={record.id} | user={user_id}")

    return {
        "optimization_id": str(record.id),
        "target_role":     target_role,
        "result":          optimization,
        "agent_error":     error,
        "optimized_at":    datetime.now(timezone.utc).isoformat(),
    }


async def get_linkedin_history(user_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the user's past LinkedIn optimization runs, most recent first."""
    rows = await db.execute(
        select(LinkedInOptimization)
        .where(LinkedInOptimization.user_id == uuid.UUID(user_id))
        .order_by(desc(LinkedInOptimization.created_at))
        .limit(limit)
    )
    records = rows.scalars().all()
    return [
        {
            "optimization_id": str(r.id),
            "target_role":     r.target_role,
            "current_score":   r.current_score,
            "optimized_score": r.optimized_score,
            "created_at":      r.created_at.isoformat(),
        }
        for r in records
    ]
