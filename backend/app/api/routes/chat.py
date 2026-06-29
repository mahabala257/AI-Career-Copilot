"""
app/api/routes/chat.py — Conversational AI career assistant.

This is a focused, grounded chat: it loads the user's real profile (skills,
resume ATS, skill gaps) from the DB, retrieves relevant knowledge-base context
(job requirements, career guidance, company info), and makes ONE LLM call to
answer the question directly and conversationally.

Why one call instead of the full multi-agent graph? The dedicated feature pages
already use the graph (supervisor → specialist → synthesizer). For a chatbot,
the synthesizer's templated status summary ("resume analyzed, N gaps…") is not a
real answer — and routing through 2-3 agents is slow and rate-limit-heavy on the
free tier. A single grounded call gives a genuine, fast, specific reply.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.sanitize import sanitize_user_text
from app.db.database import get_db
from app.llm.gemini_client import get_gemini_flash
from app.models.user import User
from app.rag.retriever import (
    retrieve_career_guidance,
    retrieve_company_information,
    retrieve_job_requirements,
)
from app.services.user_context import load_user_agent_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])


CHAT_SYSTEM = """You are AI Career Copilot's assistant — a warm, encouraging, and genuinely
helpful career mentor for students and job seekers (primarily in India). Talk like a
supportive senior who's been there: friendly, human, and motivating, never robotic.

Style:
- Conversational and natural, like a helpful chat — greet warmly when it fits, use the
  person's first name occasionally if you know it.
- Be specific and practical. When asked about companies, name real companies and the exact
  roles/teams. When giving steps, use short "- " bullet points.
- Acknowledge feelings if the person sounds stressed or discouraged, then guide them forward.
- Ground answers in the user's profile and the reference context. If something isn't there,
  use realistic general knowledge of the current job market.
- Keep it focused (usually under ~250 words). End with a short, friendly follow-up question or
  a clear next step so the conversation flows.
- Plain text only — no markdown headings or JSON. Remember the earlier messages in this chat."""


class ChatTurn(BaseModel):
    role:    str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message:     str = Field(..., min_length=1, max_length=2000)
    target_role: str | None = None
    history:     list[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply:               str
    agents_used:         list[str]
    recommendations:     list[str]
    primary_output_type: str | None = None
    generated_at:        str


def _fmt(items, limit=12):
    items = [str(x) for x in (items or []) if str(x).strip()][:limit]
    return ", ".join(items) if items else "—"


@router.post("/message", response_model=ChatResponse, summary="Chat with the AI career assistant")
async def chat_message(
    body: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    target_role = body.target_role or current_user.target_role or "a tech role"
    message = sanitize_user_text(body.message, max_len=2000)

    # ── Ground in the user's real profile ──────────────────────────────────────
    ctx = await load_user_agent_context(str(current_user.id), db)
    resume = ctx.get("resume_analysis") or {}
    skills = ctx.get("current_skills") or []
    gaps   = (ctx.get("skill_gap_analysis") or {}).get("missing_skills") or resume.get("missing_skills") or []
    ats    = resume.get("ats_score")

    # ── Retrieve relevant knowledge-base context (best-effort) ─────────────────
    # Kept small + truncated to stay well under the free-tier per-minute token
    # limit (which was causing chat to fail with rate-limit errors).
    chunks: list[str] = []
    try:
        chunks += await retrieve_job_requirements(target_role, n_results=1)
        chunks += await retrieve_career_guidance(message, n_results=2)
        chunks += await retrieve_company_information(message, n_results=1)
    except Exception as e:  # RAG must never break chat
        logger.warning(f"[ChatRoute] RAG lookup failed (non-fatal): {e}")
    rag_block = "\n".join(f"- {c[:300]}" for c in chunks[:3]) if chunks else "(no extra context found)"

    profile = (
        f"- Name: {current_user.name or 'the user'}\n"
        f"- Target role: {target_role}\n"
        f"- Current skills: {_fmt(skills)}\n"
        f"- Resume ATS score: {ats if ats is not None else 'not analysed yet'}\n"
        f"- Known skill gaps: {_fmt(gaps)}"
    )
    system_full = (
        f"{CHAT_SYSTEM}\n\n"
        f"ABOUT THE PERSON YOU'RE TALKING TO:\n{profile}\n\n"
        f"REFERENCE CONTEXT (from the knowledge base, use if relevant):\n{rag_block}"
    )

    # Build the conversation: system + recent history + the new message, so the
    # assistant remembers the chat and follow-up questions work naturally.
    messages = [SystemMessage(content=system_full)]
    for turn in body.history[-6:]:
        text = (turn.content or "").strip()
        if not text:
            continue
        if turn.role == "assistant":
            messages.append(AIMessage(content=text[:2000]))
        else:
            messages.append(HumanMessage(content=sanitize_user_text(text, max_len=2000)))
    messages.append(HumanMessage(content=message))

    try:
        llm = get_gemini_flash()
        response = await llm.ainvoke(messages)
        reply = (response.content or "").strip() or (
            "I couldn't generate a response just now — please try rephrasing."
        )
    except Exception as e:
        logger.error(f"[ChatRoute] LLM failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The assistant is busy right now (rate limit). Please try again in a moment.",
        )

    return ChatResponse(
        reply=reply,
        agents_used=[],
        recommendations=[],
        primary_output_type="chat",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
