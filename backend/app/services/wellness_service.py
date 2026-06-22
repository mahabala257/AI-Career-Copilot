"""
app/services/wellness_service.py
───────────────────────────────────
Business logic for wellness check-ins.
Orchestrates: LangGraph invocation → DB persistence → response shaping.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.agents.graph import get_graph
from app.agents.state import create_initial_state
from app.models.phase3_models import WellnessCheckin

logger = logging.getLogger(__name__)


async def run_wellness_checkin(
    *,
    user_id: str,
    session_id: str,
    mood_message: str,
    target_role: str,
    db: AsyncSession,
) -> dict:
    """Invoke Wellness Agent via LangGraph and persist the result."""
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=mood_message,
        target_role=target_role,
        mood_message=mood_message,
    )

    logger.info(f"[WellnessService] Invoking LangGraph | user={user_id}")

    graph  = get_graph()
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": session_id}},
    )

    wellness_output = result.get("wellness_output", {})
    error           = result.get("error")

    burnout_level = wellness_output.get("burnout_risk", {}).get("level")
    help_flag     = wellness_output.get("professional_help_flag", False)

    record = WellnessCheckin(
        user_id=user_id,
        mood_message=mood_message,
        burnout_risk_level=burnout_level,
        response_data=wellness_output,
        professional_help_flag=help_flag,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        f"[WellnessService] Persisted | id={record.id} | "
        f"burnout={burnout_level} | help_flag={help_flag} | user={user_id}"
    )

    return {
        "checkin_id":    str(record.id),
        "result":         wellness_output,
        "agent_error":    error,
        "checked_in_at":  datetime.now(timezone.utc).isoformat(),
    }


async def get_wellness_history(user_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the user's past wellness check-ins, most recent first."""
    rows = await db.execute(
        select(WellnessCheckin)
        .where(WellnessCheckin.user_id == user_id)
        .order_by(desc(WellnessCheckin.created_at))
        .limit(limit)
    )
    records = rows.scalars().all()
    return [
        {
            "checkin_id":          str(r.id),
            "burnout_risk_level":  r.burnout_risk_level,
            "created_at":          r.created_at.isoformat(),
        }
        for r in records
    ]
