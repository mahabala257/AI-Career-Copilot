"""
app/services/interview_service.py
───────────────────────────────────
Service layer for interview operations.
Orchestrates LangGraph invocation + DB persistence + session management.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_graph
from app.agents.interview.interview_agent import evaluate_answers
from app.agents.state import AgentName, create_initial_state
from app.models.models import InterviewSession

logger = logging.getLogger(__name__)


async def run_interview_generation(
    *,
    user_id: str,
    session_id: str,
    target_role: str,
    interview_type: str,
    difficulty: str,
    db: AsyncSession,
) -> dict:
    """
    Generate interview questions via LangGraph and persist the session to DB.
    Returns the full output dict plus the DB session_id for answer submission.
    """
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Generate {interview_type} interview questions for {target_role}",
        target_role=target_role,
        interview_type=interview_type,
    )
    initial_state["quiz_difficulty"] = difficulty  # type: ignore[index]
    initial_state["next_agent"]      = AgentName.INTERVIEW  # type: ignore[index]
    initial_state["agent_queue"]     = []  # type: ignore[index]

    result = await get_graph().ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )

    output = result.get("interview_output", {})
    error  = result.get("error")

    # Persist session to DB so answers can be submitted later
    interview_session = InterviewSession(
        user_id=uuid.UUID(user_id),
        session_type=interview_type,
        target_role=target_role,
        questions=output.get("questions", []),
    )
    db.add(interview_session)
    await db.commit()
    await db.refresh(interview_session)

    db_session_id = str(interview_session.id)
    logger.info(
        f"[InterviewService] Session created | id={db_session_id} | "
        f"type={interview_type} | questions={len(output.get('questions', []))}"
    )

    return {
        "session_id":   db_session_id,
        "agent_error":  error,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **output,
    }


async def run_answer_evaluation(
    *,
    db_session_id: str,
    user_id: str,
    answers: list[dict],
    target_role: str,
    db: AsyncSession,
) -> dict:
    """
    Evaluate submitted answers against stored questions.
    Persists the readiness score back to the InterviewSession record.
    """
    # Load the interview session
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id      == uuid.UUID(db_session_id),
            InterviewSession.user_id == uuid.UUID(user_id),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError(f"Interview session '{db_session_id}' not found")

    questions = session.questions or []
    evaluation = await evaluate_answers(
        questions=questions,
        answers=answers,
        target_role=target_role,
    )

    # Persist score + feedback. Only store a positive score: an overall_score of
    # 0 means the evaluation failed (e.g. rate-limited) or no real answers were
    # given — saving it would wipe a previously good score on the dashboard.
    score = evaluation.get("overall_score", 0)
    session.feedback = evaluation
    if isinstance(score, (int, float)) and score > 0:
        session.readiness_score = int(score)
    await db.commit()

    return {
        **evaluation,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_interview_history(
    user_id: str,
    db: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == uuid.UUID(user_id))
        .order_by(desc(InterviewSession.created_at))
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "session_id":      str(s.id),
            "session_type":    s.session_type,
            "target_role":     s.target_role or "",
            "readiness_score": s.readiness_score,
            "created_at":      s.created_at.isoformat(),
        }
        for s in sessions
    ]
