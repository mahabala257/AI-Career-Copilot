"""
app/services/company_service.py
─────────────────────────────────
Business logic for company research.
Orchestrates: LangGraph invocation → DB persistence → response shaping.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.agents.graph import get_graph
from app.agents.state import create_initial_state
from app.models.phase3_models import CompanyResearch

logger = logging.getLogger(__name__)


async def run_company_research(
    *,
    user_id: str,
    session_id: str,
    company_name: str,
    target_role: str,
    db: AsyncSession,
) -> dict:
    """Invoke Company Research Agent via LangGraph and persist the result."""
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Research {company_name} for a {target_role} role",
        target_role=target_role,
        company_name=company_name,
    )

    logger.info(f"[CompanyService] Invoking LangGraph | user={user_id} | company={company_name}")

    graph  = get_graph()
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": session_id}},
    )

    research = result.get("company_research_output", {})
    error    = result.get("error")

    alignment_score = research.get("skill_alignment", {}).get("alignment_score")

    record = CompanyResearch(
        user_id=user_id,
        company_name=company_name,
        target_role=target_role,
        alignment_score=alignment_score,
        research_data=research,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(f"[CompanyService] Persisted | id={record.id} | user={user_id}")

    return {
        "research_id":  str(record.id),
        "company_name": company_name,
        "target_role":  target_role,
        "result":        research,
        "agent_error":   error,
        "researched_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_company_history(user_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the user's past company research runs, most recent first."""
    rows = await db.execute(
        select(CompanyResearch)
        .where(CompanyResearch.user_id == user_id)
        .order_by(desc(CompanyResearch.created_at))
        .limit(limit)
    )
    records = rows.scalars().all()
    return [
        {
            "research_id":     str(r.id),
            "company_name":    r.company_name,
            "target_role":     r.target_role,
            "alignment_score": r.alignment_score,
            "created_at":      r.created_at.isoformat(),
        }
        for r in records
    ]
