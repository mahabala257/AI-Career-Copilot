"""
app/services/internship_service.py
─────────────────────────────────────
Business logic for internship research.
Orchestrates: LangGraph invocation → DB persistence → response shaping.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

import uuid
from app.agents.graph import get_graph
from app.agents.state import AgentName, create_initial_state
from app.models.phase3_models import InternshipResearch

logger = logging.getLogger(__name__)


async def run_internship_research(
    *,
    user_id: str,
    session_id: str,
    target_role: str,
    education_level: str,
    college_tier: str,
    available_from: str,
    duration_months: int | None = None,
    db: AsyncSession,
) -> dict:
    """Invoke Internship Research Agent via LangGraph and persist the result."""
    # Fold the preferred duration into the availability context + message so the
    # agent recommends internships matching that length.
    avail = available_from
    dur_msg = ""
    if duration_months:
        dur_msg = f", preferring ~{duration_months}-month internships"
        avail = (f"{available_from}, " if available_from else "") + f"~{duration_months} month duration"

    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Find internships for {target_role}, {education_level}{dur_msg}",
        target_role=target_role,
        education_level=education_level,
        college_tier=college_tier,
        available_from=avail,
    )
    initial_state["next_agent"]  = AgentName.INTERNSHIP_RESEARCH  # type: ignore[index]
    initial_state["agent_queue"] = []  # type: ignore[index]

    logger.info(
        f"[InternshipService] Invoking LangGraph | user={user_id} | "
        f"role={target_role} | tier={college_tier}"
    )

    graph  = get_graph()
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )

    research = result.get("internship_research_output", {})
    error    = result.get("error")

    record = InternshipResearch(
        user_id=uuid.UUID(user_id),
        target_role=target_role,
        education_level=education_level,
        college_tier=college_tier,
        available_from=available_from,
        research_data=research,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(f"[InternshipService] Persisted | id={record.id} | user={user_id}")

    return {
        "research_id":      str(record.id),
        "target_role":       target_role,
        "education_level":   education_level,
        "result":             research,
        "agent_error":        error,
        "researched_at":      datetime.now(timezone.utc).isoformat(),
    }


async def get_internship_history(user_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the user's past internship research runs, most recent first."""
    rows = await db.execute(
        select(InternshipResearch)
        .where(InternshipResearch.user_id == uuid.UUID(user_id))
        .order_by(desc(InternshipResearch.created_at))
        .limit(limit)
    )
    records = rows.scalars().all()
    return [
        {
            "research_id":     str(r.id),
            "target_role":      r.target_role,
            "education_level":  r.education_level,
            "created_at":       r.created_at.isoformat(),
        }
        for r in records
    ]
