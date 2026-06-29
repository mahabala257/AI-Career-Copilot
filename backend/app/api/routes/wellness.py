"""app/api/routes/wellness.py — Wellness & Motivation API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.wellness import (
    BurnoutRisk,
    AdjustedStudyPlan,
    CrisisResources,
    WellnessCheckinRequest,
    WellnessCheckinResponse,
    WellnessHistoryItem,
    WellnessResult,
)
from app.services.wellness_service import get_wellness_history, run_wellness_checkin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/wellness", tags=["Wellness"])


@router.post(
    "/checkin",
    response_model=WellnessCheckinResponse,
    summary="Submit an emotional check-in for support and motivation",
)
async def wellness_checkin(
    body: WellnessCheckinRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WellnessCheckinResponse:
    """
    Share how you're feeling during your career preparation journey.
    Returns emotional validation, a grounded reframe, one specific action
    for today, and burnout risk assessment.

    IMPORTANT: This is not a substitute for professional mental health support.
    If the message contains crisis signals, crisis resources are returned immediately.
    """
    target_role = current_user.target_role or ""

    try:
        data = await run_wellness_checkin(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            mood_message=body.mood_message,
            target_role=target_role,
            db=db,
        )
    except Exception as e:
        logger.error(f"[WellnessRoute] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Wellness check-in failed. Please try again.",
        )

    raw = data["result"]

    crisis_raw = raw.get("crisis_resources")
    crisis = CrisisResources(**crisis_raw) if isinstance(crisis_raw, dict) else None

    result = WellnessResult(
        emotional_validation=raw.get("emotional_validation", ""),
        reframe=raw.get("reframe", ""),
        next_single_action=raw.get("next_single_action", ""),
        progress_acknowledgment=raw.get("progress_acknowledgment", ""),
        burnout_risk=BurnoutRisk(**raw.get("burnout_risk", {})),
        motivational_quote=raw.get("motivational_quote", ""),
        weekly_reflection_prompt=raw.get("weekly_reflection_prompt", ""),
        adjusted_study_plan=AdjustedStudyPlan(**raw.get("adjusted_study_plan", {})),
        career_perspective=raw.get("career_perspective", ""),
        professional_help_note=raw.get("professional_help_note"),
        professional_help_flag=raw.get("professional_help_flag", False),
        crisis_resources=crisis,
        error_reason=raw.get("error_reason"),
    )

    return WellnessCheckinResponse(
        checkin_id=data["checkin_id"],
        result=result,
        agent_error=data.get("agent_error"),
        checked_in_at=data["checked_in_at"],
    )


@router.get(
    "/history",
    response_model=list[WellnessHistoryItem],
    summary="Get past wellness check-ins",
)
async def wellness_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[WellnessHistoryItem]:
    records = await get_wellness_history(str(current_user.id), db)
    return [WellnessHistoryItem(**r) for r in records]
