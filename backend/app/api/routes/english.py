"""app/api/routes/english.py — Spoken English Coach API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.english import (
    EnglishEvaluateRequest,
    EnglishEvaluateResponse,
    EnglishEvaluationResult,
    EnglishScores,
    StarCompliance,
    PracticeScripts,
    EnglishIssue,
    Annotation,
    VocabularyUpgrade,
    EnglishHistoryItem,
    ScriptGenerateRequest,
    ScriptGenerateResponse,
)
from app.services.english_service import (
    get_english_history,
    run_english_doubt,
    run_english_evaluation,
    run_script_generation,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/english", tags=["English Coach"])


class DoubtTurn(BaseModel):
    role:    str
    content: str


class DoubtRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history:  list[DoubtTurn] = Field(default_factory=list)


class DoubtResponse(BaseModel):
    answer:   str
    asked_at: str


@router.post("/ask", response_model=DoubtResponse, summary="Ask the English coach a question")
async def ask_doubt(
    body: DoubtRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DoubtResponse:
    try:
        data = await run_english_doubt(
            user_id=str(current_user.id),
            question=body.question,
            history=[t.model_dump() for t in body.history],
            target_role=current_user.target_role or "a tech role",
            db=db,
        )
    except Exception as e:
        logger.error(f"[EnglishRoute] Ask failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The coach is busy right now. Please try again in a moment.",
        )
    return DoubtResponse(answer=data["answer"], asked_at=data["asked_at"])


@router.post(
    "/evaluate",
    response_model=EnglishEvaluateResponse,
    summary="Evaluate spoken/written English and get corrections",
)
async def evaluate_english(
    body: EnglishEvaluateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EnglishEvaluateResponse:
    """
    Submit a spoken answer transcript or written text for professional English evaluation.
    Returns: corrected version, grammar/fluency scores, issue annotations,
    STAR compliance check, and personalised practice scripts.
    """
    target_role = current_user.target_role or "Software Engineer"

    try:
        data = await run_english_evaluation(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            spoken_text=body.spoken_text,
            context_type=body.context_type,
            question=body.question,
            target_role=target_role,
            db=db,
        )
    except Exception as e:
        logger.error(f"[EnglishRoute] Evaluate failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="English evaluation failed. Please try again.",
        )

    raw = data["result"]
    scores_raw = raw.get("scores", {})

    result = EnglishEvaluationResult(
        original_text=raw.get("original_text", body.spoken_text[:200]),
        corrected_text=raw.get("corrected_text", ""),
        scores=EnglishScores(**scores_raw) if scores_raw else EnglishScores(),
        issues=[EnglishIssue(**i) for i in raw.get("issues", [])],
        annotations=[Annotation(**a) for a in raw.get("annotations", [])],
        star_compliance=StarCompliance(**raw.get("star_compliance", {})),
        vocabulary_upgrades=[VocabularyUpgrade(**v) for v in raw.get("vocabulary_upgrades", [])],
        practice_scripts=PracticeScripts(**raw.get("practice_scripts", {}))
            if isinstance(raw.get("practice_scripts"), dict) else PracticeScripts(),
        top_3_improvements=raw.get("top_3_improvements", []),
        encouragement=raw.get("encouragement", ""),
        error_reason=raw.get("error_reason"),
    )

    return EnglishEvaluateResponse(
        evaluation_id=data["evaluation_id"],
        context_type=data["context_type"],
        result=result,
        agent_error=data.get("agent_error"),
        evaluated_at=data["evaluated_at"],
    )


@router.post(
    "/scripts",
    response_model=ScriptGenerateResponse,
    summary="Generate personalised interview practice scripts",
)
async def generate_scripts(
    body: ScriptGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ScriptGenerateResponse:
    """
    Generate a personalised elevator pitch, 2-minute self-introduction,
    and model answers to common HR questions — tailored to the user's
    background and target role.
    """
    target_role = current_user.target_role or "Software Engineer"

    try:
        data = await run_script_generation(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            target_role=target_role,
            experience_level=body.experience_level,
            db=db,
        )
    except Exception as e:
        logger.error(f"[EnglishRoute] Scripts failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Script generation failed. Please try again.",
        )

    scripts_raw = data.get("scripts", {})
    return ScriptGenerateResponse(
        scripts=PracticeScripts(**scripts_raw) if isinstance(scripts_raw, dict) else PracticeScripts(),
        generated_at=data["generated_at"],
    )


@router.get(
    "/history",
    response_model=list[EnglishHistoryItem],
    summary="Get past English evaluation sessions",
)
async def english_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[EnglishHistoryItem]:
    records = await get_english_history(str(current_user.id), db)
    return [EnglishHistoryItem(**r) for r in records]
