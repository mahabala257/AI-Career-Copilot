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

    # ── Defensive response shaping ─────────────────────────────────────────────
    # The LLM (especially the fast 8b model) can return slightly off-schema JSON:
    # numbers as strings ("2-3"), bare strings instead of objects, alternate keys.
    # Coerce/guard everything so a sloppy response degrades gracefully into a
    # partial result instead of throwing a 500.
    def _int(v, default):
        try:
            return int(v)
        except (TypeError, ValueError):
            import re as _re
            m = _re.search(r"\d+", str(v or ""))
            return int(m.group()) if m else default

    def _list(v):
        return v if isinstance(v, list) else []

    projects = []
    for p in _list(raw.get("recommended_projects")):
        if not isinstance(p, dict):
            continue
        ts = p.get("tech_stack") if isinstance(p.get("tech_stack"), dict) else {}
        try:
            projects.append(RecommendedProject(
                rank=_int(p.get("rank", len(projects) + 1), len(projects) + 1),
                title=str(p.get("title", "") or ""),
                one_liner=str(p.get("one_liner", "") or ""),
                description=str(p.get("description", "") or ""),
                why_this_impresses=str(p.get("why_this_impresses", "") or ""),
                skills_demonstrated=_list(p.get("skills_demonstrated")),
                skills_learned=_list(p.get("skills_learned")),
                estimated_weeks=_int(p.get("estimated_weeks", 2), 2),
                difficulty=str(p.get("difficulty", "intermediate") or "intermediate"),
                tech_stack=TechStack(
                    backend=_list(ts.get("backend")),
                    frontend=_list(ts.get("frontend")),
                    ai_ml=_list(ts.get("ai_ml")),
                    database=_list(ts.get("database")),
                    devops=_list(ts.get("devops")),
                ),
                github_readme_sections=_list(p.get("github_readme_sections")),
                interview_talking_points=_list(p.get("interview_talking_points")),
                scale_question=str(p.get("scale_question", "") or ""),
                demo_tip=str(p.get("demo_tip", "") or ""),
            ))
        except Exception as e:
            logger.warning(f"[ProjectsRoute] Skipping malformed project item: {e}")

    avoid = []
    for a in _list(raw.get("projects_to_avoid")):
        if isinstance(a, dict):
            name = a.get("project") or a.get("name") or a.get("project_name") or ""
            if name:
                avoid.append(ProjectToAvoid(project=str(name), reason=str(a.get("reason") or a.get("why") or "")))
        elif isinstance(a, str) and a.strip():
            avoid.append(ProjectToAvoid(project=a.strip(), reason=""))

    result = ProjectRecommendationResult(
        portfolio_score=_int(raw.get("portfolio_score", 0), 0),
        portfolio_assessment=str(raw.get("portfolio_assessment", "") or ""),
        recommended_projects=projects,
        projects_to_avoid=avoid,
        portfolio_target_score=_int(raw.get("portfolio_target_score", 75), 75),
        portfolio_action_plan=_list(raw.get("portfolio_action_plan")),
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
