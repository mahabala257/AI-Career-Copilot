"""app/api/routes/linkedin.py — LinkedIn Optimization API endpoints."""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.linkedin import (
    LinkedInHistoryItem,
    LinkedInOptimizeRequest,
    LinkedInOptimizeResponse,
    LinkedInOptimizationResult,
    LinkedInSections,
    HeadlineSection,
    AboutSection,
    SkillsReorder,
    KeywordDensity,
)
from app.services.linkedin_service import get_linkedin_history, run_linkedin_optimization

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/linkedin", tags=["LinkedIn"])


@router.post(
    "/optimize",
    response_model=LinkedInOptimizeResponse,
    summary="Optimize LinkedIn profile sections",
)
async def optimize_linkedin(
    body: LinkedInOptimizeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LinkedInOptimizeResponse:
    """
    Analyze and rewrite LinkedIn headline, About section, and experience bullets
    for the user's target role. Returns optimized text with scoring and keyword analysis.
    """
    try:
        data = await run_linkedin_optimization(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            headline=body.headline,
            about=body.about,
            experience=body.experience,
            skills=body.skills,
            target_role=body.target_role,
            db=db,
        )
    except Exception as e:
        logger.error(f"[LinkedInRoute] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LinkedIn optimization failed. Please try again.",
        )

    raw = data["result"]
    raw_sections = raw.get("sections", {})

    result = LinkedInOptimizationResult(
        current_score=raw.get("current_score", 0),
        optimized_score=raw.get("optimized_score", 0),
        score_breakdown=raw.get("score_breakdown", {}),
        sections=LinkedInSections(
            headline=HeadlineSection(**raw_sections.get("headline", {})),
            about=AboutSection(**raw_sections.get("about", {})),
            experience_bullets=raw_sections.get("experience_bullets", []),
            skills_reorder=SkillsReorder(**raw_sections.get("skills_reorder", {})),
        ),
        keyword_density=KeywordDensity(**raw.get("keyword_density", {})),
        top_3_changes=raw.get("top_3_changes", []),
        creator_tips=raw.get("creator_tips", []),
        profile_completeness_tips=raw.get("profile_completeness_tips", []),
        error_reason=raw.get("error_reason"),
    )

    return LinkedInOptimizeResponse(
        optimization_id=data["optimization_id"],
        target_role=data["target_role"],
        result=result,
        agent_error=data.get("agent_error"),
        optimized_at=data["optimized_at"],
    )


@router.get(
    "/history",
    response_model=list[LinkedInHistoryItem],
    summary="Get past LinkedIn optimization runs",
)
async def linkedin_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[LinkedInHistoryItem]:
    records = await get_linkedin_history(str(current_user.id), db)
    return [LinkedInHistoryItem(**r) for r in records]
