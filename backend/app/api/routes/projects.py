"""app/api/routes/projects.py — Project Recommendation API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectHistoryItem,
    ProjectRecommendRequest,
    ProjectRecommendResponse,
    ProjectRecommendationResult,
    RecommendedProject,
    TechStack,
    ProjectToAvoid,
)
from app.services.project_service import get_project_history, run_project_recommendations

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post(
    "/recommend",
    response_model=ProjectRecommendResponse,
    summary="Get personalised project recommendations",
)
async def recommend_projects(
    body: ProjectRecommendRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRecommendResponse:
    """
    Recommend 3 tailored portfolio projects based on the user's target role,
    experience level, skill gaps, and existing resume projects.
    """
    try:
        data = await run_project_recommendations(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            target_role=body.target_role,
            experience_level=body.experience_level,
            time_available_weeks=body.time_available_weeks,
            db=db,
        )
    except Exception as e:
        logger.error(f"[ProjectsRoute] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project recommendation failed. Please try again.",
        )

    raw = data["result"]

    projects = []
    for p in raw.get("recommended_projects", []):
        ts = p.get("tech_stack", {})
        projects.append(RecommendedProject(
            rank=p.get("rank", 1),
            title=p.get("title", ""),
            one_liner=p.get("one_liner", ""),
            description=p.get("description", ""),
            why_this_impresses=p.get("why_this_impresses", ""),
            skills_demonstrated=p.get("skills_demonstrated", []),
            skills_learned=p.get("skills_learned", []),
            estimated_weeks=p.get("estimated_weeks", 2),
            difficulty=p.get("difficulty", "intermediate"),
            tech_stack=TechStack(
                backend=ts.get("backend", []),
                frontend=ts.get("frontend", []),
                ai_ml=ts.get("ai_ml", []),
                database=ts.get("database", []),
                devops=ts.get("devops", []),
            ),
            github_readme_sections=p.get("github_readme_sections", []),
            interview_talking_points=p.get("interview_talking_points", []),
            scale_question=p.get("scale_question", ""),
            demo_tip=p.get("demo_tip", ""),
        ))

    avoid = [ProjectToAvoid(**a) for a in raw.get("projects_to_avoid", [])]

    result = ProjectRecommendationResult(
        portfolio_score=raw.get("portfolio_score", 0),
        portfolio_assessment=raw.get("portfolio_assessment", ""),
        recommended_projects=projects,
        projects_to_avoid=avoid,
        portfolio_target_score=raw.get("portfolio_target_score", 75),
        portfolio_action_plan=raw.get("portfolio_action_plan", []),
        error_reason=raw.get("error_reason"),
    )

    return ProjectRecommendResponse(
        recommendation_id=data["recommendation_id"],
        target_role=data["target_role"],
        experience_level=data["experience_level"],
        result=result,
        agent_error=data.get("agent_error"),
        generated_at=data["generated_at"],
    )


@router.get(
    "/history",
    response_model=list[ProjectHistoryItem],
    summary="Get past project recommendation runs",
)
async def project_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectHistoryItem]:
    records = await get_project_history(str(current_user.id), db)
    return [ProjectHistoryItem(**r) for r in records]
