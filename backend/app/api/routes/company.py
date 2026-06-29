"""app/api/routes/company.py — Company Research API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.company import (
    CompanyHistoryItem,
    CompanyResearchRequest,
    CompanyResearchResponse,
    CompanyResearchResult,
    InterviewRound,
    KnownQuestion,
    SkillAlignment,
    PrepStrategyWeek,
    TypicalOpening,
)
from app.services.company_service import get_company_history, run_company_research

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/company", tags=["Company Research"])


@router.post(
    "/research",
    response_model=CompanyResearchResponse,
    summary="Research a target company",
)
async def research_company(
    body: CompanyResearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResearchResponse:
    """
    Research a target company: tech stack, interview process, culture,
    known question types, skill alignment, and a week-by-week prep strategy.
    """
    try:
        data = await run_company_research(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            company_name=body.company_name,
            target_role=body.target_role,
            work_mode=body.work_mode or "Any",
            employment_type=body.employment_type or "Any",
            db=db,
        )
    except Exception as e:
        logger.error(f"[CompanyRoute] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Company research failed. Please try again.",
        )

    raw = data["result"]

    result = CompanyResearchResult(
        company_name=raw.get("company_name", body.company_name),
        company_type=raw.get("company_type", ""),
        overview=raw.get("overview", ""),
        tech_stack=raw.get("tech_stack", []),
        engineering_culture=raw.get("engineering_culture", ""),
        interview_style=raw.get("interview_style", ""),
        interview_rounds=[InterviewRound(**r) for r in raw.get("interview_rounds", [])],
        culture_values=raw.get("culture_values", []),
        known_question_types=[KnownQuestion(**q) for q in raw.get("known_question_types", [])],
        skill_alignment=SkillAlignment(**raw.get("skill_alignment", {})),
        prep_strategy=[PrepStrategyWeek(**w) for w in raw.get("prep_strategy", [])],
        typical_timeline=raw.get("typical_timeline", ""),
        salary_range=raw.get("salary_range", ""),
        pros=raw.get("pros", []),
        cons=raw.get("cons", []),
        glassdoor_rating=raw.get("glassdoor_rating"),
        application_tips=raw.get("application_tips", []),
        typical_openings=[TypicalOpening(**o) for o in raw.get("typical_openings", [])],
        error_reason=raw.get("error_reason"),
    )

    return CompanyResearchResponse(
        research_id=data["research_id"],
        company_name=data["company_name"],
        target_role=data["target_role"],
        result=result,
        agent_error=data.get("agent_error"),
        researched_at=data["researched_at"],
    )


@router.get(
    "/history",
    response_model=list[CompanyHistoryItem],
    summary="Get past company research runs",
)
async def company_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[CompanyHistoryItem]:
    records = await get_company_history(str(current_user.id), db)
    return [CompanyHistoryItem(**r) for r in records]
