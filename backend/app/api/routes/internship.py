"""app/api/routes/internship.py — Internship Research API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.internship import (
    InternshipHistoryItem,
    InternshipResearchRequest,
    InternshipResearchResponse,
    InternshipResearchResult,
    RecommendedInternship,
    CoverLetterOutline,
    PreparationPriority,
)
from app.services.internship_service import get_internship_history, run_internship_research

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/internship", tags=["Internship Research"])


@router.post(
    "/research",
    response_model=InternshipResearchResponse,
    summary="Research internship opportunities",
)
async def research_internships(
    body: InternshipResearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> InternshipResearchResponse:
    """
    Recommend realistic internship companies based on target role,
    education level, and college tier, with application timeline
    and cover letter outline.
    """
    try:
        data = await run_internship_research(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            target_role=body.target_role,
            education_level=body.education_level,
            college_tier=body.college_tier,
            available_from=body.available_from,
            duration_months=body.duration_months,
            db=db,
        )
    except Exception as e:
        logger.error(f"[InternshipRoute] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internship research failed. Please try again.",
        )

    raw = data["result"]

    companies = [RecommendedInternship(**c) for c in raw.get("recommended_companies", [])]
    priorities = [PreparationPriority(**p) for p in raw.get("preparation_priorities", [])]

    cover_letter_raw = raw.get("cover_letter_outline", {})
    cover_letter = CoverLetterOutline(**cover_letter_raw) if isinstance(cover_letter_raw, dict) else CoverLetterOutline()

    result = InternshipResearchResult(
        student_profile_summary=raw.get("student_profile_summary", ""),
        recommended_companies=companies,
        application_timeline=raw.get("application_timeline", {}),
        cover_letter_outline=cover_letter,
        skill_gaps_for_internships=raw.get("skill_gaps_for_internships", []),
        preparation_priorities=priorities,
        top_platforms=raw.get("top_platforms", []),
        resume_tips_for_internships=raw.get("resume_tips_for_internships", []),
        networking_tips=raw.get("networking_tips", []),
        common_mistakes=raw.get("common_mistakes", []),
        error_reason=raw.get("error_reason"),
    )

    return InternshipResearchResponse(
        research_id=data["research_id"],
        target_role=data["target_role"],
        education_level=data["education_level"],
        result=result,
        agent_error=data.get("agent_error"),
        researched_at=data["researched_at"],
    )


@router.get(
    "/history",
    response_model=list[InternshipHistoryItem],
    summary="Get past internship research runs",
)
async def internship_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[InternshipHistoryItem]:
    records = await get_internship_history(str(current_user.id), db)
    return [InternshipHistoryItem(**r) for r in records]
