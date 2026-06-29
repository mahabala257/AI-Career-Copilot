"""
app/services/english_service.py
─────────────────────────────────
Business logic for spoken English evaluation.
Orchestrates: LangGraph invocation → DB persistence → response shaping.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

import uuid
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.agents.graph import get_graph
from app.agents.state import AgentName, create_initial_state
from app.core.sanitize import sanitize_user_text
from app.llm.gemini_client import get_gemini_flash
from app.models.phase2_models import EnglishEvaluation

logger = logging.getLogger(__name__)


async def run_english_evaluation(
    *,
    user_id: str,
    session_id: str,
    spoken_text: str,
    context_type: str,
    question: str,
    target_role: str,
    db: AsyncSession,
) -> dict:
    """
    Invoke Spoken English Agent via LangGraph and persist result.
    """
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Evaluate my English for a {context_type}",
        target_role=target_role,
        spoken_text=sanitize_user_text(spoken_text, max_len=5000),
        english_context_type=context_type,
        question_answered=sanitize_user_text(question, max_len=500),
    )
    initial_state["next_agent"]  = AgentName.SPOKEN_ENGLISH  # type: ignore[index]
    initial_state["agent_queue"] = []  # type: ignore[index]

    logger.info(
        f"[EnglishService] Invoking LangGraph | user={user_id} | "
        f"context={context_type} | text_len={len(spoken_text)}"
    )

    graph  = get_graph()
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )

    evaluation = result.get("english_output", {})
    error      = result.get("error")

    # ── Persist to DB ──────────────────────────────────────────────────────────
    scores    = evaluation.get("scores", {})
    record    = EnglishEvaluation(
        user_id=uuid.UUID(user_id),
        original_text=spoken_text,
        corrected_text=evaluation.get("corrected_text", ""),
        context_type=context_type,
        question_answered=question,
        overall_score=scores.get("overall"),
        scores_breakdown=scores,
        issues=evaluation.get("issues", []),
        star_compliance=evaluation.get("star_compliance", {}),
        practice_scripts=evaluation.get("practice_scripts", {}),
        vocabulary_upgrades=evaluation.get("vocabulary_upgrades", []),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        f"[EnglishService] Persisted | id={record.id} | "
        f"score={record.overall_score} | user={user_id}"
    )

    return {
        "evaluation_id": str(record.id),
        "context_type":  context_type,
        "result":        evaluation,
        "agent_error":   error,
        "evaluated_at":  datetime.now(timezone.utc).isoformat(),
    }


async def run_script_generation(
    *,
    user_id: str,
    session_id: str,
    target_role: str,
    experience_level: str,
    db: AsyncSession,
) -> dict:
    """
    Generate practice scripts without evaluating input text.
    The English Agent switches to script-generation mode when spoken_text is empty.
    """
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message="Generate my interview practice scripts",
        target_role=target_role,
        spoken_text="",          # empty → agent switches to script mode
        experience_level=experience_level,
        english_context_type="self_intro",
    )
    initial_state["next_agent"]  = AgentName.SPOKEN_ENGLISH  # type: ignore[index]
    initial_state["agent_queue"] = []  # type: ignore[index]

    graph  = get_graph()
    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": f"{session_id}:{uuid.uuid4().hex[:8]}"}},
    )

    english_output = result.get("english_output", {})
    scripts        = english_output.get("practice_scripts", {})

    return {
        "scripts":      scripts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_english_history(user_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the user's past English evaluations, most recent first."""
    rows = await db.execute(
        select(EnglishEvaluation)
        .where(EnglishEvaluation.user_id == uuid.UUID(user_id))
        .order_by(desc(EnglishEvaluation.created_at))
        .limit(limit)
    )
    records = rows.scalars().all()
    return [
        {
            "evaluation_id": str(r.id),
            "context_type":  r.context_type,
            "overall_score": r.overall_score,
            "created_at":    r.created_at.isoformat(),
        }
        for r in records
    ]


# ── Ask a Doubt (conversational English coaching) ───────────────────────────────
ENGLISH_COACH_PERSONA = """You are a warm, encouraging spoken-English and interview-communication
coach for students and job seekers (primarily in India). Answer the student's question clearly,
kindly, and practically. Give concrete examples and short "- " bullet tips when useful.
Plain text only — no markdown headings or JSON. Keep it focused (~200 words). Remember the
earlier messages in this conversation so follow-ups make sense."""


async def run_english_doubt(
    *,
    user_id: str,
    question: str,
    history: list[dict] | None,
    target_role: str,
    db: AsyncSession,
) -> dict:
    """Answer an open English/communication question conversationally (one LLM call)."""
    # Optional grounding: the student's most recent evaluation score
    ctx = ""
    try:
        latest = (
            await db.execute(
                select(EnglishEvaluation)
                .where(EnglishEvaluation.user_id == uuid.UUID(user_id))
                .order_by(desc(EnglishEvaluation.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest and latest.overall_score is not None:
            ctx = f"\n\nFor context, the student's most recent practice answer scored {latest.overall_score}/100."
    except Exception:
        pass

    system = f"{ENGLISH_COACH_PERSONA}{ctx}\n\nThe student is targeting the role: {target_role}."
    messages = [SystemMessage(content=system)]
    for turn in (history or [])[-8:]:
        text = (turn.get("content") or "").strip()
        if not text:
            continue
        if turn.get("role") == "assistant":
            messages.append(AIMessage(content=text[:2000]))
        else:
            messages.append(HumanMessage(content=sanitize_user_text(text, max_len=2000)))
    messages.append(HumanMessage(content=sanitize_user_text(question, max_len=2000)))

    llm = get_gemini_flash()
    response = await llm.ainvoke(messages)
    answer = (response.content or "").strip() or "Could you rephrase that? I want to make sure I help correctly."

    logger.info(f"[EnglishService] Doubt answered | user={user_id}")
    return {"answer": answer, "asked_at": datetime.now(timezone.utc).isoformat()}
