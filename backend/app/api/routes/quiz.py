"""app/api/routes/quiz.py — Quiz API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.quiz import QuizGenerateResponse, QuizRequest, QuizScoreResponse, QuizSubmitRequest
from app.services.quiz_service import run_quiz_generation, run_quiz_scoring

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.post("/generate", response_model=QuizGenerateResponse, summary="Generate a quiz")
async def generate_quiz(
    body: QuizRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizGenerateResponse:
    try:
        result = await run_quiz_generation(
            user_id=str(current_user.id), session_id=str(current_user.id),
            topic=body.topic, difficulty=body.difficulty, quiz_type=body.quiz_type, db=db,
        )
    except Exception as e:
        logger.error(f"[QuizRoute] Generate failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Quiz generation failed. Please try again.")
    return QuizGenerateResponse(**result)


@router.post("/submit", response_model=QuizScoreResponse, summary="Submit answers for scoring")
async def submit_quiz(
    body: QuizSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizScoreResponse:
    try:
        result = await run_quiz_scoring(
            quiz_id=body.quiz_id, user_id=str(current_user.id),
            answers=[a.model_dump() for a in body.answers], db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"[QuizRoute] Submit failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Quiz scoring failed. Please try again.")
    return QuizScoreResponse(**result)
