"""
app/agents/personal/linkedin_agent.py
──────────────────────────────────────
LinkedIn Optimization Agent — LangGraph node implementation.

Reads from state:
  linkedin_headline, linkedin_about, linkedin_experience, linkedin_skills
  target_role, resume_analysis (for skill context)
  rag_context (injected by enrich_state_with_rag before LLM call)

Writes to state:
  linkedin_output   — full optimization result
  agents_called     — appends AgentName.LINKEDIN
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.personal.linkedin_prompts import (
    LINKEDIN_SYSTEM,
    build_linkedin_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def linkedin_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    LangGraph node: LinkedIn Optimization Agent.
    Analyzes the user's LinkedIn sections and returns rewritten,
    optimized versions with scoring and keyword analysis.
    """
    logger.info(f"[LinkedInAgent] Starting | user={state.get('user_id')} | role={state.get('target_role')}")

    # ── Extract inputs from state ──────────────────────────────────────────────
    headline    = state.get("linkedin_headline", "")
    about       = state.get("linkedin_about", "")
    experience  = state.get("linkedin_experience", "")
    skills      = state.get("linkedin_skills", [])
    target_role = state.get("target_role", "Software Engineer")

    # Pull existing skills from resume analysis if LinkedIn skills not provided
    if not skills:
        resume = state.get("resume_analysis", {})
        skills = resume.get("extracted_skills", [])

    # Guard: need at least one section to optimize
    if not any([headline, about, experience]):
        logger.warning("[LinkedInAgent] No LinkedIn content provided")
        return {
            "linkedin_output": _fallback_output("No LinkedIn profile content was provided. Please paste at least your headline or About section."),
            "agents_called": [AgentName.LINKEDIN],
        }

    # ── RAG enrichment ─────────────────────────────────────────────────────────
    rag_update  = await enrich_state_with_rag(state, AgentName.LINKEDIN)
    rag_context = rag_update.get("rag_context", [])
    logger.info(f"[LinkedInAgent] RAG retrieved {len(rag_context)} chunks")

    # ── Build and call Gemini ──────────────────────────────────────────────────
    try:
        llm = get_gemini_flash()
        human_prompt = build_linkedin_prompt(
            headline=headline,
            about=about,
            experience=experience,
            skills=skills,
            target_role=target_role,
            rag_context=rag_context,
        )

        response = await llm.ainvoke([
            SystemMessage(content=LINKEDIN_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        raw = response.content
        logger.debug(f"[LinkedInAgent] Raw response (first 300): {raw[:300]}")

        result = _parse_linkedin_response(raw)

        # Populate section originals if agent didn't echo them back
        if "sections" in result and "headline" in result["sections"]:
            if not result["sections"]["headline"].get("current"):
                result["sections"]["headline"]["current"] = headline

        logger.info(
            f"[LinkedInAgent] Done | score {result.get('current_score')} → "
            f"{result.get('optimized_score')} | user={state.get('user_id')}"
        )
        return {
            "linkedin_output": result,
            "agents_called": [AgentName.LINKEDIN],
        }

    except Exception as e:
        logger.error(f"[LinkedInAgent] Failed: {e}", exc_info=True)
        return {
            "linkedin_output": _fallback_output(f"LinkedIn optimization failed: {str(e)}"),
            "error": str(e),
            "error_agent": AgentName.LINKEDIN,
            "agents_called": [AgentName.LINKEDIN],
        }


def _parse_linkedin_response(raw: str) -> dict:
    """Parse Gemini JSON response with fence stripping and fallback."""
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

    # Find the JSON object
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]

    try:
        data = json.loads(cleaned)
        return _validate_linkedin_output(data)
    except json.JSONDecodeError as e:
        logger.error(f"[LinkedInAgent] JSON parse error: {e} | raw: {cleaned[:200]}")
        return _fallback_output("Could not parse optimization response. Please try again.")


def _validate_linkedin_output(data: dict) -> dict:
    """Ensure required fields exist with safe defaults."""
    data.setdefault("current_score", 50)
    data.setdefault("optimized_score", 75)
    data.setdefault("score_breakdown", {})
    data.setdefault("sections", {})
    data.setdefault("keyword_density", {
        "present_keywords": [],
        "missing_high_value_keywords": [],
        "keyword_score": 50,
    })
    data.setdefault("top_3_changes", [])
    data.setdefault("creator_tips", [])
    data.setdefault("profile_completeness_tips", [])

    sections = data["sections"]
    sections.setdefault("headline", {"current": "", "optimized": "", "reasoning": ""})
    sections.setdefault("about", {"current_summary": "", "optimized": "", "hook_score": 50, "reasoning": ""})
    sections.setdefault("experience_bullets", [])
    sections.setdefault("skills_reorder", {
        "recommended_top_3": [],
        "skills_to_add": [],
        "skills_to_remove": [],
        "reasoning": "",
    })
    return data


def _fallback_output(error_message: str) -> dict:
    return {
        "current_score": 0,
        "optimized_score": 0,
        "score_breakdown": {},
        "sections": {
            "headline": {"current": "", "optimized": "", "reasoning": ""},
            "about": {"current_summary": "", "optimized": "", "hook_score": 0, "reasoning": ""},
            "experience_bullets": [],
            "skills_reorder": {"recommended_top_3": [], "skills_to_add": [], "skills_to_remove": [], "reasoning": ""},
        },
        "keyword_density": {"present_keywords": [], "missing_high_value_keywords": [], "keyword_score": 0},
        "top_3_changes": [],
        "creator_tips": [],
        "profile_completeness_tips": [],
        "error_reason": error_message,
    }
