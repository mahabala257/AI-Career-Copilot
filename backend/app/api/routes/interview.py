"""
app/api/routes/interview.py
────────────────────────────
Interview API endpoints.

POST /api/interview/generate   — Generate questions
POST /api/interview/evaluate   — Submit answers for scoring
GET  /api/interview/history    — Past sessions
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.interview import (
    EvaluateRequest, EvaluationResponse,
    InterviewRequest, InterviewResponse,
    InterviewHistoryItem,
)
from app.services.interview_service import (
    get_interview_history,
    run_answer_evaluation,
    run_interview_generation,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview", tags=["Interview"])


@router.post(
    "/generate",
    response_model=InterviewResponse,
    summary="Generate interview questions for a target role",
)
async def generate_interview(
    body: InterviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewResponse:
    try:
        result = await run_interview_generation(
            user_id=str(current_user.id),
            session_id=str(current_user.id),
            target_role=body.target_role,
            interview_type=body.interview_type,
            difficulty=body.difficulty,
            db=db,
        )
    except Exception as e:
        logger.error(f"[InterviewRoute] Generate failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interview generation failed. Please try again.",
        )
    return InterviewResponse(**result)


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    summary="Submit answers for AI evaluation and scoring",
)
async def evaluate_interview(
    body: EvaluateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    try:
        result = await run_answer_evaluation(
            db_session_id=body.session_id,
            user_id=str(current_user.id),
            answers=[a.model_dump() for a in body.answers],
            target_role=body.target_role,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"[InterviewRoute] Evaluate failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation failed. Please try again.",
        )
    return EvaluationResponse(**result)


@router.get(
    "/history",
    response_model=list[InterviewHistoryItem],
    summary="Get past interview sessions",
)
async def interview_history(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[InterviewHistoryItem]:
    items = await get_interview_history(str(current_user.id), db, limit)
    return [InterviewHistoryItem(**i) for i in items]
