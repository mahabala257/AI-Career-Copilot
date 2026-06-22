"""
app/agents/career/resume_agent.py
───────────────────────────────────
Production Resume Agent — replaces the stub in placeholders.py.

What this agent does
─────────────────────
  1. Reads resume_text from state (already extracted from PDF by the API layer)
  2. Queries ChromaDB for job requirements matching target_role (RAG)
  3. Calls Gemini with a structured analysis prompt
  4. Parses and validates the JSON response
  5. Computes a final weighted ATS score from component scores
  6. Updates state with resume_analysis dict

LangGraph contract
───────────────────
  Input state fields read:
    - state["resume_text"]     — required, extracted PDF text
    - state["target_role"]     — required, e.g. "AI Engineer"
    - state["user_id"]         — for logging
    - state["rag_context"]     — optional, pre-loaded by RAG layer

  Output state fields written:
    - state["resume_analysis"] — full analysis dict
    - state["agents_called"]   — appends AgentName.RESUME
    - state["error"]           — set on failure (doesn't crash graph)
    - state["error_agent"]     — set on failure

Error handling strategy
────────────────────────
  - JSON parse error → try to extract partial data, fill rest with defaults
  - LLM API error   → return empty analysis with error recorded in state
  - Missing resume  → return validation error in state
  In all cases: write error to state and continue — never raise unhandled exceptions
  from a LangGraph node (it would crash the entire graph for this session).
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.career.resume_prompts import (
    RESUME_ANALYSIS_SYSTEM,
    build_resume_analysis_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


# ── Main agent node ────────────────────────────────────────────────────────────

async def resume_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Resume Agent LangGraph node.
    Registered in graph.py as: graph.add_node(AgentName.RESUME, resume_agent_node)
    """
    user_id = state.get("user_id", "unknown")
    target_role = state.get("target_role", "Software Engineer")
    resume_text = state.get("resume_text", "")
    # rag_context already set from enrich_state_with_rag above

    logger.info(f"[ResumeAgent] Starting | user={user_id} | role={target_role}")

    # ── Enrich state with RAG context ──────────────────────────────────────────
    rag_update = await enrich_state_with_rag(state, AgentName.RESUME)
    rag_context = rag_update.get("rag_context", [])

    # ── Validate input ─────────────────────────────────────────────────────────
    if not resume_text or len(resume_text.strip()) < 50:
        logger.warning(f"[ResumeAgent] Insufficient resume text ({len(resume_text)} chars)")
        return {
            "resume_analysis": _empty_analysis(
                reason="No resume text provided. Please upload your resume PDF first.",
                target_role=target_role,
            ),
            "agents_called": [AgentName.RESUME],
            "error": "Resume text missing or too short",
            "error_agent": AgentName.RESUME,
        }

    # ── Call Gemini ────────────────────────────────────────────────────────────
    try:
        llm = get_gemini_flash()

        human_prompt = build_resume_analysis_prompt(
            resume_text=resume_text,
            target_role=target_role,
            rag_context=rag_context,
        )

        logger.debug(f"[ResumeAgent] Sending {len(human_prompt)} chars to Gemini")

        response = await llm.ainvoke([
            SystemMessage(content=RESUME_ANALYSIS_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        raw = response.content
        logger.debug(f"[ResumeAgent] Gemini raw response ({len(raw)} chars): {raw[:200]}")

    except Exception as e:
        logger.error(f"[ResumeAgent] Gemini call failed: {e}", exc_info=True)
        return {
            "resume_analysis": _empty_analysis(
                reason=f"AI analysis temporarily unavailable: {str(e)[:100]}",
                target_role=target_role,
            ),
            "agents_called": [AgentName.RESUME],
            "error": f"ResumeAgent LLM error: {str(e)[:200]}",
            "error_agent": AgentName.RESUME,
        }

    # ── Parse response ─────────────────────────────────────────────────────────
    try:
        analysis = _parse_analysis_response(raw)
    except Exception as e:
        logger.error(f"[ResumeAgent] Parse failed: {e}. Raw: {raw[:300]}")
        return {
            "resume_analysis": _empty_analysis(
                reason="Could not parse analysis response. Please try again.",
                target_role=target_role,
            ),
            "agents_called": [AgentName.RESUME],
            "error": f"ResumeAgent parse error: {str(e)[:200]}",
            "error_agent": AgentName.RESUME,
        }

    # ── Enrich and validate ────────────────────────────────────────────────────
    analysis = _enrich_analysis(analysis, target_role, resume_text)

    logger.info(
        f"[ResumeAgent] Done | ats_score={analysis.get('ats_score')} | "
        f"skills={len(analysis.get('extracted_skills', []))} | "
        f"missing={len(analysis.get('missing_skills', []))}"
    )

    return {
        "resume_analysis": analysis,
        "agents_called": [AgentName.RESUME],
    }


# ── Parsing helpers ────────────────────────────────────────────────────────────

def _parse_analysis_response(raw: str) -> dict[str, Any]:
    """
    Parse Gemini's JSON response robustly.

    Handles:
      - Clean JSON (ideal)
      - JSON wrapped in ```json ... ``` markdown fences
      - JSON with trailing commas (common LLM mistake)
      - JSON buried in surrounding text
    """
    # Step 1: strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

    # Step 2: find the outermost JSON object
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")

    json_str = text[start:end]

    # Step 3: fix trailing commas (e.g. ["a", "b",] )
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    return json.loads(json_str)


def _enrich_analysis(
    raw: dict[str, Any],
    target_role: str,
    resume_text: str,
) -> dict[str, Any]:
    """
    Validate, normalise, and enrich the parsed analysis dict.

    Ensures:
      - All required keys exist with sensible defaults
      - Scores are clamped to [0, 100]
      - Lists contain only non-empty strings
      - Adds computed fields the API layer and frontend expect
    """
    def clamp(val, lo=0, hi=100):
        try:
            return max(lo, min(hi, int(val)))
        except (TypeError, ValueError):
            return 0

    def clean_list(lst, default=None):
        if not isinstance(lst, list):
            return default or []
        return [str(item).strip() for item in lst if str(item).strip()]

    # Core scores
    ats_score = clamp(raw.get("ats_score", 0))

    score_breakdown = raw.get("score_breakdown", {})
    breakdown = {
        "skills_match":          clamp(score_breakdown.get("skills_match", 0)),
        "experience_relevance":  clamp(score_breakdown.get("experience_relevance", 0)),
        "education_fit":         clamp(score_breakdown.get("education_fit", 0)),
        "keyword_optimization":  clamp(score_breakdown.get("keyword_optimization", 0)),
        "formatting_clarity":    clamp(score_breakdown.get("formatting_clarity", 0)),
    }

    # If breakdown exists but ats_score is 0, compute a weighted average
    if ats_score == 0 and any(breakdown.values()):
        weights = {
            "skills_match":         0.35,
            "experience_relevance": 0.25,
            "education_fit":        0.15,
            "keyword_optimization": 0.15,
            "formatting_clarity":   0.10,
        }
        ats_score = int(sum(
            breakdown[k] * weights[k] for k in weights
        ))

    extracted_skills = clean_list(raw.get("extracted_skills"), ["Not extracted"])
    missing_skills   = clean_list(raw.get("missing_skills"), [])
    strengths        = clean_list(raw.get("strengths"), ["Analysis incomplete"])
    suggestions      = clean_list(raw.get("suggestions"), ["No suggestions generated"])
    critical_missing = clean_list(raw.get("critical_missing"), missing_skills[:3])
    top_matching     = clean_list(raw.get("top_matching_skills"), extracted_skills[:5])

    experience_level = raw.get("experience_level", "unknown")
    if experience_level not in ("fresher", "junior", "mid", "senior"):
        experience_level = _infer_experience_level(resume_text)

    return {
        # Primary score
        "ats_score": ats_score,

        # Skills
        "extracted_skills":   extracted_skills,
        "missing_skills":     missing_skills,
        "top_matching_skills": top_matching,
        "critical_missing":   critical_missing,

        # Qualitative
        "strengths":          strengths,
        "suggestions":        suggestions,
        "experience_level":   experience_level,
        "improvement_priority": raw.get("improvement_priority", "skills"),

        # Component scores (0-100 each)
        "score_breakdown":    breakdown,
        "education_match":    clamp(raw.get("education_match", 0)),
        "keyword_density_score": clamp(raw.get("keyword_density_score", 0)),
        "format_score":       clamp(raw.get("format_score", 0)),

        # Context
        "target_role":        target_role,
        "analysis_source":    "gemini",
    }


def _infer_experience_level(resume_text: str) -> str:
    """Simple keyword-based fallback for experience level detection."""
    text = resume_text.lower()
    if any(w in text for w in ["10+ years", "12 years", "15 years", "senior", "lead", "principal"]):
        return "senior"
    if any(w in text for w in ["5+ years", "6 years", "7 years", "8 years", "mid-level"]):
        return "mid"
    if any(w in text for w in ["2 years", "3 years", "4 years", "junior"]):
        return "junior"
    return "fresher"


def _empty_analysis(reason: str, target_role: str) -> dict[str, Any]:
    """
    Returns a safe empty analysis dict when the agent cannot produce results.
    The frontend handles this gracefully — shows an error message with reason.
    """
    return {
        "ats_score": 0,
        "extracted_skills": [],
        "missing_skills": [],
        "top_matching_skills": [],
        "critical_missing": [],
        "strengths": [],
        "suggestions": [reason],
        "experience_level": "unknown",
        "improvement_priority": "unknown",
        "score_breakdown": {
            "skills_match": 0,
            "experience_relevance": 0,
            "education_fit": 0,
            "keyword_optimization": 0,
            "formatting_clarity": 0,
        },
        "education_match": 0,
        "keyword_density_score": 0,
        "format_score": 0,
        "target_role": target_role,
        "analysis_source": "error",
        "error_reason": reason,
    }
