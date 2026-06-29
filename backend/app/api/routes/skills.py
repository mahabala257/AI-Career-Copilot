"""
app/api/routes/skills.py
─────────────────────────
Skill gap API endpoints.

POST /api/skills/analyze  — Run full skill gap analysis
GET  /api/skills/profile  — Get current user's skills + target role
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.skill_gap import SkillGapRequest, SkillGapResponse
from app.services.skill_gap_service import run_skill_gap_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/skills", tags=["Skill Gap"])


@router.post(
    "/analyze",
    response_model=SkillGapResponse,
    summary="Analyze skill gaps for a target role",
)
async def analyze_skill_gap(
    body: SkillGapRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SkillGapResponse:
    # Merge body skills with what's already on the user profile
    profile_skills = current_user.current_skills or []
    merged = list(dict.fromkeys(profile_skills + body.current_skills))

    try:
        result = await run_skill_gap_analysis(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            target_role=body.target_role,
            current_skills=merged,
            generate_learning_path=body.generate_learning_path,
            generate_roadmap=body.generate_roadmap,
            available_hours=body.available_hours,
            db=db,
        )
    except Exception as e:
        logger.error(f"[SkillsRoute] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Skill gap analysis failed. Please try again.",
        )

    return SkillGapResponse(**result)


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get current user's skills and target role",
)
async def get_skill_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)
