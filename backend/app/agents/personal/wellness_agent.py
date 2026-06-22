"""app/agents/personal/wellness_agent.py
──────────────────────────────────────
Wellness & Motivation Agent — LangGraph node.

This agent handles the most sensitive content in the system.
Crisis detection runs BEFORE any LLM call so serious signals
get immediate crisis resources without any LLM latency.

Reads from state:
  mood_message, target_role, user_id
  rag_context (injected by enrich_state_with_rag)

Writes to state:
  wellness_output
  agents_called — appends AgentName.WELLNESS
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.personal.wellness_prompts import (
    CRISIS_RESPONSE,
    WELLNESS_SYSTEM,
    build_wellness_prompt,
    detect_crisis,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def wellness_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    LangGraph node: Wellness & Motivation Agent.

    Flow:
    1. Pre-screen for crisis keywords → return crisis response immediately if found
    2. RAG enrichment with wellness resources
    3. Gemini call for empathetic, personalised response
    4. Parse and validate JSON output
    """
    mood_message = state.get("mood_message", "").strip()
    target_role  = state.get("target_role", "")
    user_id      = state.get("user_id", "")

    logger.info(
        f"[WellnessAgent] Starting | user={user_id} | "
        f"message_len={len(mood_message)}"
    )

    if not mood_message:
        return {
            "wellness_output": _fallback_output(
                "No message provided. Please share what you're feeling."
            ),
            "agents_called": [AgentName.WELLNESS],
        }

    # ── CRITICAL: Crisis pre-screen ────────────────────────────────────────────
    # Run before ANY LLM call — crisis support must never be delayed by API latency
    if detect_crisis(mood_message):
        logger.warning(
            f"[WellnessAgent] CRISIS DETECTED | user={user_id} | "
            f"message_preview={mood_message[:50]}"
        )
        return {
            "wellness_output": CRISIS_RESPONSE,
            "agents_called": [AgentName.WELLNESS],
        }

    # ── RAG enrichment ─────────────────────────────────────────────────────────
    rag_update  = await enrich_state_with_rag(state, AgentName.WELLNESS)
    rag_context = rag_update.get("rag_context", [])

    try:
        llm = get_gemini_flash()
        human_prompt = build_wellness_prompt(
            mood_message=mood_message,
            target_role=target_role,
            career_score=None,           # Could be fetched from DB in future
            sessions_this_week=0,
            recent_failures=0,
            rag_context=rag_context,
        )

        response = await llm.ainvoke([
            SystemMessage(content=WELLNESS_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        result = _parse_response(response.content)

        # Post-process: if LLM set professional_help_flag, log for monitoring
        if result.get("professional_help_flag"):
            logger.warning(
                f"[WellnessAgent] professional_help_flag=True | user={user_id}"
            )

        logger.info(
            f"[WellnessAgent] Done | "
            f"burnout={result.get('burnout_risk', {}).get('level')} | "
            f"help_flag={result.get('professional_help_flag')} | "
            f"user={user_id}"
        )
        return {
            "wellness_output": result,
            "agents_called": [AgentName.WELLNESS],
        }

    except Exception as e:
        logger.error(f"[WellnessAgent] Failed: {e}", exc_info=True)
        return {
            "wellness_output": _fallback_output(str(e)),
            "error": str(e),
            "error_agent": AgentName.WELLNESS,
            "agents_called": [AgentName.WELLNESS],
        }


def _parse_response(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    start   = cleaned.find("{")
    end     = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    try:
        return _validate(json.loads(cleaned))
    except json.JSONDecodeError as e:
        logger.error(f"[WellnessAgent] JSON parse error: {e}")
        return _fallback_output("Could not parse wellness response. Please try again.")


def _validate(data: dict) -> dict:
    data.setdefault("emotional_validation",     "")
    data.setdefault("reframe",                  "")
    data.setdefault("next_single_action",       "")
    data.setdefault("progress_acknowledgment",  "")
    data.setdefault("burnout_risk",             {"level": "low", "signals": [], "recommendation": ""})
    data.setdefault("motivational_quote",       "")
    data.setdefault("weekly_reflection_prompt", "")
    data.setdefault("adjusted_study_plan",      {"recommendation": "", "reason": ""})
    data.setdefault("career_perspective",       "")
    data.setdefault("professional_help_note",   None)
    data.setdefault("professional_help_flag",   False)
    data.setdefault("crisis_resources",         None)
    return data


def _fallback_output(error_message: str) -> dict:
    return {
        "emotional_validation": "I'm here to listen.",
        "reframe": "", "next_single_action": "",
        "progress_acknowledgment": "", "career_perspective": "",
        "burnout_risk": {"level": "unknown", "signals": [], "recommendation": ""},
        "motivational_quote": "", "weekly_reflection_prompt": "",
        "adjusted_study_plan": {"recommendation": "", "reason": ""},
        "professional_help_note": None, "professional_help_flag": False,
        "crisis_resources": None, "error_reason": error_message,
    }
