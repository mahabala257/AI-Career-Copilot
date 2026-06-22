"""
app/agents/career/skill_gap_agent.py
──────────────────────────────────────
Production Skill Gap Agent — replaces the stub in placeholders.py.

What makes this agent different from the Resume Agent
───────────────────────────────────────────────────────
The Resume Agent analyses what the candidate HAS.
This agent analyses the DELTA between what they have and what the market needs.

It has two input modes:

  Mode 1 — After Resume Agent (most common):
    state["resume_analysis"] is populated. We read extracted_skills from it.
    The agent compares those against job requirements from ChromaDB.

  Mode 2 — Direct request (no resume uploaded):
    state["current_skills"] or state from user profile.
    Still produces a valid gap analysis, just without resume context.

Why reading from resume_analysis matters
──────────────────────────────────────────
The Resume Agent already made an expensive Gemini call to extract skills.
We MUST reuse that work instead of asking Gemini to re-extract from the
raw resume text. This is the core of the multi-agent value — each agent
stands on the shoulders of the previous one.

Chain:
  Resume Agent → extracted_skills → Skill Gap Agent → missing_skills
                                                     → Study Planner Agent (Step 7)

Optional extended outputs
──────────────────────────
If state["generate_learning_path"] is True, the agent makes a second Gemini
call to produce detailed per-skill learning paths. This is off by default
because it doubles token cost — only used when the user explicitly asks
for a full roadmap.
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.career.skill_gap_prompts import (
    LEARNING_PATH_SYSTEM,
    ROADMAP_SYSTEM,
    SKILL_GAP_ANALYSIS_SYSTEM,
    build_learning_path_prompt,
    build_roadmap_prompt,
    build_skill_gap_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def skill_gap_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Skill Gap Agent LangGraph node.
    Registered in graph.py as: graph.add_node(AgentName.SKILL_GAP, skill_gap_agent_node)
    """
    user_id     = state.get("user_id", "unknown")
    target_role = state.get("target_role", "")
    rag_context = state.get("rag_context", [])

    # Read skills from state — prefer resume analysis output, fall back to profile
    resume_analysis  = state.get("resume_analysis", {})
    current_skills   = state.get("current_skills", [])  # from user profile
    # Merge: profile skills + resume extracted skills (deduped)
    resume_skills    = resume_analysis.get("extracted_skills", [])
    merged_skills    = _merge_skills(current_skills, resume_skills)

    logger.info(
        f"[SkillGapAgent] Starting | user={user_id} | role={target_role} | "
        f"skills_count={len(merged_skills)}"
    )

    # ── Enrich state with RAG context ──────────────────────────────────────────
    rag_update  = await enrich_state_with_rag(state, AgentName.SKILL_GAP)
    rag_context = rag_update.get("rag_context", [])

    if not target_role:
        logger.warning("[SkillGapAgent] No target_role in state")
        return {
            "skill_gap_analysis": _empty_analysis("No target role specified. Please set your target role first."),
            "agents_called": [AgentName.SKILL_GAP],
            "error": "SkillGapAgent: target_role missing",
            "error_agent": AgentName.SKILL_GAP,
        }

    # ── Main skill gap analysis ────────────────────────────────────────────────
    analysis = await _run_skill_gap_analysis(
        current_skills=merged_skills,
        target_role=target_role,
        rag_context=rag_context,
        resume_analysis=resume_analysis,
    )

    # ── Optional: detailed learning paths ─────────────────────────────────────
    # Only generated when user explicitly requests a full roadmap
    learning_paths = {}
    if state.get("generate_learning_path") and analysis.get("missing_skills"):
        missing_names = [
            s["skill"] if isinstance(s, dict) else s
            for s in analysis["missing_skills"][:8]
        ]
        learning_paths = await _run_learning_path(
            missing_skills=missing_names,
            target_role=target_role,
            available_hours=state.get("available_hours", 2.0),
        )

    # ── Optional: timeline roadmap ─────────────────────────────────────────────
    roadmap = {}
    if state.get("generate_roadmap") and analysis.get("missing_skills"):
        missing_names = [
            s["skill"] if isinstance(s, dict) else s
            for s in analysis["missing_skills"]
        ]
        roadmap = await _run_roadmap(
            missing_skills=missing_names,
            current_skills=merged_skills,
            target_role=target_role,
        )

    # Attach optional outputs into the analysis dict
    if learning_paths:
        analysis["learning_paths"] = learning_paths.get("learning_paths", [])
    if roadmap:
        analysis["roadmap"] = roadmap

    logger.info(
        f"[SkillGapAgent] Done | readiness={analysis.get('overall_readiness_percent')}% | "
        f"missing={len(analysis.get('missing_skills', []))} | "
        f"months_to_ready={analysis.get('months_to_job_ready')}"
    )

    return {
        "skill_gap_analysis": analysis,
        "agents_called": [AgentName.SKILL_GAP],
    }


# ── Core analysis call ────────────────────────────────────────────────────────

async def _run_skill_gap_analysis(
    current_skills: list[str],
    target_role: str,
    rag_context: list[str],
    resume_analysis: dict,
) -> dict[str, Any]:
    """Call Gemini for the primary skill gap analysis."""
    try:
        llm = get_gemini_flash()
        human_prompt = build_skill_gap_prompt(
            current_skills=current_skills,
            target_role=target_role,
            rag_context=rag_context,
            resume_analysis=resume_analysis,
        )

        logger.debug(f"[SkillGapAgent] Prompt length: {len(human_prompt)} chars")

        response = await llm.ainvoke([
            SystemMessage(content=SKILL_GAP_ANALYSIS_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        raw = response.content
        logger.debug(f"[SkillGapAgent] Raw response preview: {raw[:200]}")

        parsed  = _parse_json_response(raw)
        enriched = _enrich_analysis(parsed, current_skills, target_role)
        return enriched

    except Exception as e:
        logger.error(f"[SkillGapAgent] Analysis failed: {e}", exc_info=True)
        return _empty_analysis(
            reason=f"Skill gap analysis temporarily unavailable: {str(e)[:120]}",
            current_skills=current_skills,
            target_role=target_role,
        )


async def _run_learning_path(
    missing_skills: list[str],
    target_role: str,
    available_hours: float,
) -> dict[str, Any]:
    """Optional second call for detailed learning paths per skill."""
    try:
        llm = get_gemini_flash()
        response = await llm.ainvoke([
            SystemMessage(content=LEARNING_PATH_SYSTEM),
            HumanMessage(content=build_learning_path_prompt(
                missing_skills=missing_skills,
                target_role=target_role,
                available_hours_per_day=available_hours,
            )),
        ])
        return _parse_json_response(response.content)
    except Exception as e:
        logger.error(f"[SkillGapAgent] Learning path failed: {e}")
        return {}


async def _run_roadmap(
    missing_skills: list[str],
    current_skills: list[str],
    target_role: str,
) -> dict[str, Any]:
    """Optional third call for timeline roadmap."""
    try:
        llm = get_gemini_flash()
        response = await llm.ainvoke([
            SystemMessage(content=ROADMAP_SYSTEM),
            HumanMessage(content=build_roadmap_prompt(
                missing_skills=missing_skills,
                target_role=target_role,
                current_skills=current_skills,
            )),
        ])
        return _parse_json_response(response.content)
    except Exception as e:
        logger.error(f"[SkillGapAgent] Roadmap failed: {e}")
        return {}


# ── Parsing & enrichment ───────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict[str, Any]:
    """Robust JSON parser — handles fences, trailing commas, buried JSON."""
    text = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object in response")
    json_str = text[start:end]
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)   # fix trailing commas
    return json.loads(json_str)


def _enrich_analysis(
    raw: dict[str, Any],
    current_skills: list[str],
    target_role: str,
) -> dict[str, Any]:
    """
    Validate and normalise the parsed analysis.

    Ensures:
      - Readiness score clamped to [0, 100]
      - missing_skills is always a list of dicts with required keys
      - priority_order is a plain list of strings (for Study Planner Agent)
      - Provides safe defaults for every field the API schema expects
    """

    def clamp(v, lo=0, hi=100):
        try:
            return max(lo, min(hi, int(v)))
        except (TypeError, ValueError):
            return 0

    def clean_list(lst, default=None):
        if not isinstance(lst, list):
            return default or []
        return [str(i).strip() for i in lst if str(i).strip()]

    readiness = clamp(raw.get("overall_readiness_percent", 0))

    # Normalise missing_skills to always be a list of dicts
    raw_missing = raw.get("missing_skills", [])
    missing_skills = []
    for item in raw_missing:
        if isinstance(item, dict):
            missing_skills.append({
                "skill":              str(item.get("skill", "Unknown")).strip(),
                "category":           str(item.get("category", "general")).strip(),
                "priority":           str(item.get("priority", "medium")).strip(),
                "why_important":      str(item.get("why_important", "")).strip(),
                "time_to_learn":      str(item.get("time_to_learn", "2-4 weeks")).strip(),
                "learning_resources": clean_list(item.get("learning_resources"), []),
            })
        elif isinstance(item, str) and item.strip():
            # Gemini sometimes returns a flat string list — convert to dict
            missing_skills.append({
                "skill": item.strip(),
                "category": "general",
                "priority": "medium",
                "why_important": f"Required for {target_role} roles",
                "time_to_learn": "2-4 weeks",
                "learning_resources": [],
            })

    # priority_order as plain string list (Study Planner Agent reads this)
    raw_priority = raw.get("priority_order", [])
    if raw_priority:
        priority_order = clean_list(raw_priority)
    else:
        # Derive from missing_skills sorted by priority weight
        weight = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_missing = sorted(
            missing_skills,
            key=lambda x: weight.get(x.get("priority", "medium"), 2)
        )
        priority_order = [s["skill"] for s in sorted_missing]

    # matched_skills — normalise to list of dicts
    raw_matched = raw.get("matched_skills", [])
    matched_skills = []
    for item in raw_matched:
        if isinstance(item, dict):
            matched_skills.append({
                "skill":            str(item.get("skill", "")).strip(),
                "candidate_level":  str(item.get("candidate_level", "basic")).strip(),
                "required_level":   str(item.get("required_level", "intermediate")).strip(),
                "gap":              str(item.get("gap", "none")).strip(),
            })

    skill_categories = raw.get("skill_categories", {})
    if not isinstance(skill_categories, dict):
        skill_categories = {}

    return {
        "target_role":               target_role,
        "overall_readiness_percent": readiness,
        "current_skills":            clean_list(raw.get("current_skills"), current_skills),
        "required_skills":           clean_list(raw.get("required_skills"), []),
        "matched_skills":            matched_skills,
        "missing_skills":            missing_skills,
        "priority_order":            priority_order,
        "skill_categories": {
            "strong":               clean_list(skill_categories.get("strong"), []),
            "developing":           clean_list(skill_categories.get("developing"), []),
            "missing_critical":     clean_list(skill_categories.get("missing_critical"), []),
            "missing_nice_to_have": clean_list(skill_categories.get("missing_nice_to_have"), []),
        },
        "months_to_job_ready":       max(1, int(raw.get("months_to_job_ready", 6) or 6)),
        "immediate_actions":         clean_list(raw.get("immediate_actions"), []),
        "strengths_to_highlight":    clean_list(raw.get("strengths_to_highlight"), []),
        "analysis_source":           "gemini",
    }


def _merge_skills(profile_skills: list[str], resume_skills: list[str]) -> list[str]:
    """Deduplicated merge of skills from user profile and resume extraction."""
    seen = set()
    merged = []
    for skill in (profile_skills or []) + (resume_skills or []):
        normalised = skill.strip().lower()
        if normalised and normalised not in seen:
            seen.add(normalised)
            merged.append(skill.strip())
    return merged


def _empty_analysis(
    reason: str,
    current_skills: list[str] | None = None,
    target_role: str = "",
) -> dict[str, Any]:
    return {
        "target_role":               target_role,
        "overall_readiness_percent": 0,
        "current_skills":            current_skills or [],
        "required_skills":           [],
        "matched_skills":            [],
        "missing_skills":            [],
        "priority_order":            [],
        "skill_categories":          {"strong": [], "developing": [], "missing_critical": [], "missing_nice_to_have": []},
        "months_to_job_ready":       12,
        "immediate_actions":         [reason],
        "strengths_to_highlight":    [],
        "analysis_source":           "error",
        "error_reason":              reason,
    }
