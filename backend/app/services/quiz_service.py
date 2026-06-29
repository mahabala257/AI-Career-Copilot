"""app/services/quiz_service.py — Quiz service layer."""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_graph
from app.agents.interview.quiz_agent import score_quiz
from app.agents.state import AgentName, create_initial_state
from app.models.models import QuizResult

logger = logging.getLogger(__name__)


async def run_quiz_generation(
    *, user_id: str, session_id: str, topic: str,
    difficulty: str, quiz_type: str, db: AsyncSession,
) -> dict:
    initial_state = create_initial_state(
        user_id=user_id, session_id=session_id,
        user_message=f"Generate a {difficulty} {quiz_type} quiz on {topic or 'a relevant topic'}",
    )
    initial_state["quiz_topic"]      = topic       # type: ignore[index]
    initial_state["quiz_difficulty"] = difficulty  # type: ignore[index]
    initial_state["quiz_type"]       = quiz_type   # type: ignore[index]
    # Skip the Supervisor LLM call (saves tokens, avoids multi-agent fan-out)
    initial_state["next_agent"]      = AgentName.QUIZ  # type: ignore[index]
    initial_state["agent_queue"]     = []  # type: ignore[index]

    # Unique thread per request — these are stateless RPC calls, so we must NOT
    # resume a shared checkpoint (which would accumulate stale state across calls).
    result = await get_graph().ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )
    output = result.get("quiz_output", {})
    error  = result.get("error")

    # Persist to DB to store questions for later scoring
    record = QuizResult(
        user_id=uuid.UUID(user_id),
        topic=output.get("topic", topic or "General"),
        difficulty=difficulty,
        quiz_type=quiz_type,
        questions=output.get("questions", []),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(f"[QuizService] Generated | id={record.id} | questions={len(output.get('questions', []))}")
    return {
        "quiz_id":             str(record.id),
        "agent_error":         error,
        "generated_at":        datetime.now(timezone.utc).isoformat(),
        **output,
    }


async def run_quiz_scoring(
    *, quiz_id: str, user_id: str, answers: list[dict], db: AsyncSession,
) -> dict:
    from sqlalchemy import select
    result = await db.execute(
        select(QuizResult).where(
            QuizResult.id      == uuid.UUID(quiz_id),
            QuizResult.user_id == uuid.UUID(user_id),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise ValueError(f"Quiz '{quiz_id}' not found")

    score_result = await score_quiz(questions=record.questions or [], user_answers=answers)

    record.user_answers = answers
    record.score        = score_result.get("score_percent", 0)
    record.weak_areas   = score_result.get("weak_areas", [])
    await db.commit()

    return {
        "quiz_id":    quiz_id,
        "scored_at":  datetime.now(timezone.utc).isoformat(),
        **score_result,
    }
