"""app/api/routes/planner.py — Study Planner API endpoints."""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.models import StudyPlan
from app.models.user import User
from app.agents.graph import get_graph
from app.agents.state import AgentName, create_initial_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/planner", tags=["Study Planner"])


class PlanRequest(BaseModel):
    plan_type:       str   = Field(default="weekly", pattern="^(daily|weekly|monthly)$")
    target_role:     str   = Field(default="", max_length=100)
    available_hours: float = Field(default=2.0, ge=0.5, le=12.0)


class PlanResponse(BaseModel):
    plan_id:      str
    plan_type:    str
    target_role:  str
    plan_data:    dict
    agent_error:  str | None = None
    generated_at: str


@router.post("/generate", response_model=PlanResponse, summary="Generate a personalized study plan")
async def generate_plan(
    body: PlanRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    target_role = body.target_role or current_user.target_role or "Software Engineer"

    initial_state = create_initial_state(
        user_id=str(current_user.id),
        session_id=str(current_user.id),
        user_message=f"Create a {body.plan_type} study plan for {target_role}",
        target_role=target_role,
        plan_type=body.plan_type,
        available_hours=body.available_hours,
    )
    # Skip the Supervisor LLM call (saves tokens, deterministic routing)
    initial_state["next_agent"]  = AgentName.STUDY_PLANNER  # type: ignore[index]
    initial_state["agent_queue"] = []  # type: ignore[index]

    # Inject the user's latest resume, skill gaps and quiz weak areas so the
    # plan is grounded in real data instead of relying on cross-request memory.
    from app.services.user_context import load_user_agent_context
    ctx = await load_user_agent_context(str(current_user.id), db)
    initial_state["resume_analysis"]    = ctx["resume_analysis"]     # type: ignore[index]
    initial_state["skill_gap_analysis"] = ctx["skill_gap_analysis"]  # type: ignore[index]
    initial_state["quiz_output"]        = ctx["quiz_output"]         # type: ignore[index]
    initial_state["current_skills"]     = ctx["current_skills"]      # type: ignore[index]

    try:
        result = await get_graph().ainvoke(
            initial_state,
            config={"configurable": {"thread_id": f"{current_user.id}:{uuid.uuid4().hex[:8]}"}},
        )
    except Exception as e:
        logger.error(f"[PlannerRoute] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Study plan generation failed.")

    plan_data  = result.get("study_plan_output", {})
    error      = result.get("error")

    # Deactivate old plans of same type
    from sqlalchemy import update
    await db.execute(
        update(StudyPlan)
        .where(StudyPlan.user_id == current_user.id, StudyPlan.plan_type == body.plan_type)
        .values(is_active=False)
    )

    record = StudyPlan(
        user_id=current_user.id,
        plan_type=body.plan_type,
        target_role=target_role,
        plan_data=plan_data,
        is_active=True,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return PlanResponse(
        plan_id=str(record.id),
        plan_type=body.plan_type,
        target_role=target_role,
        plan_data=plan_data,
        agent_error=error,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/current", summary="Get the user's active study plans")
async def get_current_plan(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(
        select(StudyPlan)
        .where(StudyPlan.user_id == current_user.id, StudyPlan.is_active == True)
        .order_by(StudyPlan.created_at.desc())
        .limit(3)
    )
    plans = result.scalars().all()
    return [
        {
            "plan_id":    str(p.id),
            "plan_type":  p.plan_type,
            "target_role": p.target_role,
            "plan_data":  p.plan_data,
            "created_at": p.created_at.isoformat(),
        }
        for p in plans
    ]
