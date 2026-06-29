"""
app/agents/interview/interview_agent.py
─────────────────────────────────────────
Production Interview Agent — replaces the stub in placeholders.py.

What this agent does
─────────────────────
  Generates role-specific, difficulty-calibrated interview questions for
  three session types: HR, Technical, and Coding.

  It also evaluates candidate answers when submitted (second call).

Why Gemini (not Groq) in this implementation?
  The architecture doc planned Groq for Interview Agent (speed).
  We use Gemini here because:
    1. Gemini 2.0 Flash is fast enough (< 3s for 10 questions)
    2. Gemini produces more structured, role-calibrated output
    3. Groq integration added in Phase 2 as a speed optimisation

  To swap to Groq: change `get_gemini_flash()` to `get_groq_llm()`.
  Nothing else changes — same prompts, same parser, same state contract.

LangGraph state contract
─────────────────────────
  Reads:
    state["interview_type"]      — "hr" | "technical" | "coding"
    state["target_role"]         — e.g. "AI Engineer"
    state["quiz_difficulty"]     — reused field "easy"|"medium"|"hard"
    state["skill_gap_analysis"]  — optional, adds focus areas to technical Q's
    state["resume_analysis"]     — optional, experience level for difficulty

  Writes:
    state["interview_output"]    — full structured question set
    state["agents_called"]       — appends AgentName.INTERVIEW
    state["error"]               — on failure
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.interview.interview_prompts import (
    ANSWER_EVALUATION_SYSTEM,
    CODING_INTERVIEW_SYSTEM,
    HR_INTERVIEW_SYSTEM,
    TECHNICAL_INTERVIEW_SYSTEM,
    build_coding_prompt,
    build_evaluation_prompt,
    build_hr_prompt,
    build_technical_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)

# Default questions per session type
DEFAULT_QUESTION_COUNT = {"hr": 8, "technical": 10, "coding": 5}


async def interview_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Interview Agent LangGraph node.
    Registered in graph.py as: graph.add_node(AgentName.INTERVIEW, interview_agent_node)
    """
    user_id        = state.get("user_id", "unknown")
    target_role    = state.get("target_role", "Software Engineer")
    interview_type = state.get("interview_type", "technical")
    difficulty     = state.get("quiz_difficulty", "medium")   # reuse difficulty field
    skill_gaps     = _extract_skill_gaps(state)
    weak_areas     = _extract_weak_areas(state)
    count          = DEFAULT_QUESTION_COUNT.get(interview_type, 10)

    logger.info(
        f"[InterviewAgent] Starting | user={user_id} | "
        f"type={interview_type} | role={target_role} | difficulty={difficulty}"
    )

    # ── Enrich state with RAG context ──────────────────────────────────────────
    rag_update = await enrich_state_with_rag(state, AgentName.INTERVIEW)
    # Note: interview prompts don't currently inject rag_context but it's
    # available in state for future prompt enrichment

    if interview_type not in ("hr", "technical", "coding"):
        interview_type = "technical"
        logger.warning(f"[InterviewAgent] Unknown type, defaulting to 'technical'")

    try:
        output = await _generate_questions(
            interview_type=interview_type,
            target_role=target_role,
            difficulty=difficulty,
            count=count,
            skill_gaps=skill_gaps,
            weak_areas=weak_areas,
        )
    except Exception as e:
        logger.error(f"[InterviewAgent] Failed: {e}", exc_info=True)
        return {
            "interview_output": _empty_output(
                interview_type, target_role,
                reason=f"Question generation failed: {str(e)[:120]}"
            ),
            "agents_called": [AgentName.INTERVIEW],
            "error": f"InterviewAgent error: {str(e)[:200]}",
            "error_agent": AgentName.INTERVIEW,
        }

    logger.info(
        f"[InterviewAgent] Done | questions={len(output.get('questions', []))} | "
        f"type={interview_type}"
    )

    return {
        "interview_output": output,
        "agents_called": [AgentName.INTERVIEW],
    }


# ── Question generation dispatcher ────────────────────────────────────────────

async def _generate_questions(
    interview_type: str,
    target_role: str,
    difficulty: str,
    count: int,
    skill_gaps: list[str],
    weak_areas: list[str],
) -> dict[str, Any]:
    """Dispatch to the correct prompt builder based on interview type."""
    llm = get_gemini_flash()

    if interview_type == "hr":
        system  = HR_INTERVIEW_SYSTEM
        human   = build_hr_prompt(target_role, difficulty, count)

    elif interview_type == "coding":
        system  = CODING_INTERVIEW_SYSTEM
        human   = build_coding_prompt(target_role, difficulty, count)

    else:  # technical (default)
        system  = TECHNICAL_INTERVIEW_SYSTEM
        human   = build_technical_prompt(
            target_role=target_role,
            difficulty=difficulty,
            count=count,
            skill_gaps=skill_gaps,
            weak_areas=weak_areas,
        )

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=human),
    ])

    raw    = response.content
    parsed = _parse_json(raw)
    return _enrich_output(parsed, interview_type, target_role, difficulty)


async def evaluate_answers(
    questions: list[dict],
    answers: list[dict],
    target_role: str,
) -> dict[str, Any]:
    """
    Standalone evaluation function called by the API route when the user
    submits answers. Not a LangGraph node — called directly from the route.
    Returns structured scores and feedback.
    """
    if not questions or not answers:
        return {"error": "No questions or answers to evaluate"}

    try:
        llm    = get_gemini_flash()
        response = await llm.ainvoke([
            SystemMessage(content=ANSWER_EVALUATION_SYSTEM),
            HumanMessage(content=build_evaluation_prompt(questions, answers, target_role)),
        ])
        result = _parse_json(response.content)
        return _enrich_evaluation(result)
    except Exception as e:
        logger.error(f"[InterviewAgent] Evaluation failed: {e}")
        return {
            "evaluations": [],
            "overall_score": 0,
            "overall_grade": "needs_improvement",
            "readiness_assessment": f"Evaluation failed: {str(e)[:100]}",
            "top_improvement_areas": [],
            "interview_tips": [],
        }


# ── Parsing ────────────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict[str, Any]:
    text     = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    start    = text.find("{")
    end      = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object in response")
    json_str = re.sub(r",\s*([}\]])", r"\1", text[start:end])
    return json.loads(json_str)


def _enrich_output(
    raw: dict[str, Any],
    interview_type: str,
    target_role: str,
    difficulty: str,
) -> dict[str, Any]:
    """Validate and normalise the output dict. Ensure all required keys exist."""

    questions = raw.get("questions", [])
    if not isinstance(questions, list):
        questions = []

    # Ensure every question has an id
    for i, q in enumerate(questions, start=1):
        if isinstance(q, dict) and "id" not in q:
            q["id"] = i

    return {
        "session_type":                  interview_type,
        "role":                          target_role,
        "difficulty":                    difficulty,
        "questions":                     questions,
        "total_questions":               len(questions),
        "estimated_duration_minutes":    raw.get("total_estimated_time_minutes", len(questions) * 5),
        "preparation_tips":              raw.get("preparation_tips", []),
        "preparation_resources":         raw.get("preparation_resources", []),
        "topics_covered":                raw.get("topics_covered", raw.get("topic_distribution", {})),
        "analysis_source": "ai",
    }


def _enrich_evaluation(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalise evaluation response."""
    return {
        "evaluations":          raw.get("evaluations", []),
        "overall_score":        min(100, max(0, int(raw.get("overall_score", 0) or 0))),
        "overall_grade":        raw.get("overall_grade", "needs_improvement"),
        "readiness_assessment": raw.get("readiness_assessment", ""),
        "top_improvement_areas": raw.get("top_improvement_areas", []),
        "interview_tips":       raw.get("interview_tips", []),
    }


# ── State helpers ──────────────────────────────────────────────────────────────

def _extract_skill_gaps(state: CareerCopilotState) -> list[str]:
    """Pull priority skills from skill_gap_analysis if available."""
    skill_gap = state.get("skill_gap_analysis", {})
    if not skill_gap:
        return []
    priority = skill_gap.get("priority_order", [])
    return [s for s in priority if isinstance(s, str)][:6]


def _extract_weak_areas(state: CareerCopilotState) -> list[str]:
    """Pull weak areas from a previous quiz session if available."""
    quiz = state.get("quiz_output", {})
    if not quiz:
        return []
    return quiz.get("weak_areas", [])[:4]


def _empty_output(
    interview_type: str,
    target_role: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "session_type":               interview_type,
        "role":                       target_role,
        "difficulty":                 "medium",
        "questions":                  [],
        "total_questions":            0,
        "estimated_duration_minutes": 0,
        "preparation_tips":           [reason],
        "preparation_resources":      [],
        "topics_covered":             {},
        "analysis_source":            "error",
        "error_reason":               reason,
    }
