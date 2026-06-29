"""
app/agents/interview/quiz_agent.py
────────────────────────────────────
Production Quiz & Assessment Agent — replaces the stub in placeholders.py.

What this agent does
─────────────────────
  Phase A — Generation (LangGraph node):
    Generates MCQ or coding quiz questions for a given topic and difficulty.
    Uses weak_areas from a previous quiz session to focus on gaps.

  Phase B — Scoring (standalone function called by API):
    Takes user answers + original questions → returns score, grade, weak areas.
    Weak areas flow back into state for Study Planner and Interview Agent to use.

State contract
───────────────
  Reads:
    state["quiz_topic"]       — "Machine Learning", "Python", etc.
    state["quiz_difficulty"]  — "easy" | "medium" | "hard"
    state["quiz_type"]        — "mcq" | "coding" | "mixed" (default: mcq)
    state["quiz_output"]      — previous quiz results (for weak area focus)
    state["skill_gap_analysis"] — used to auto-select topics when quiz_topic is empty

  Writes:
    state["quiz_output"]    — generated quiz questions
    state["agents_called"]  — appends AgentName.QUIZ
    state["error"]          — on failure

Auto-topic selection
─────────────────────
If the user doesn't specify a topic, the agent picks one automatically:
  1. From skill_gap_analysis.priority_order (most impactful skill gap first)
  2. From quiz_output.next_quiz_focus (previous quiz's recommended focus)
  3. Falls back to "Computer Science Fundamentals"
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.interview.quiz_prompts import (
    CODING_QUIZ_SYSTEM,
    MCQ_SYSTEM,
    SCORING_SYSTEM,
    build_coding_quiz_prompt,
    build_mcq_prompt,
    build_scoring_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def quiz_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Quiz Agent LangGraph node.
    Registered in graph.py as: graph.add_node(AgentName.QUIZ, quiz_agent_node)
    """
    user_id    = state.get("user_id", "unknown")
    topic      = _resolve_topic(state)
    difficulty = state.get("quiz_difficulty", "medium")
    quiz_type  = state.get("quiz_type", "mcq")  # type: ignore[attr-defined]
    count      = 10 if quiz_type == "mcq" else 5

    logger.info(
        f"[QuizAgent] Starting | user={user_id} | "
        f"topic={topic} | difficulty={difficulty} | type={quiz_type}"
    )

    try:
        output = await _generate_quiz(topic, difficulty, quiz_type, count)
    except Exception as e:
        logger.error(f"[QuizAgent] Generation failed: {e}", exc_info=True)
        return {
            "quiz_output": _empty_output(topic, difficulty, str(e)[:120]),
            "agents_called": [AgentName.QUIZ],
            "error": f"QuizAgent error: {str(e)[:200]}",
            "error_agent": AgentName.QUIZ,
        }

    logger.info(
        f"[QuizAgent] Done | questions={len(output.get('questions', []))} | topic={topic}"
    )

    return {
        "quiz_output":   output,
        "agents_called": [AgentName.QUIZ],
    }


# ── Quiz generation ────────────────────────────────────────────────────────────

async def _generate_quiz(
    topic: str,
    difficulty: str,
    quiz_type: str,
    count: int,
) -> dict[str, Any]:
    """Generate a quiz using the appropriate prompt for the quiz type."""
    llm = get_gemini_flash()

    if quiz_type == "coding":
        system = CODING_QUIZ_SYSTEM
        human  = build_coding_quiz_prompt(topic, difficulty, count)
    else:  # mcq or mixed
        system = MCQ_SYSTEM
        human  = build_mcq_prompt(topic, difficulty, count)

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=human),
    ])

    parsed  = _parse_json(response.content)
    return _enrich_quiz_output(parsed, topic, difficulty, quiz_type)


# ── Answer scoring (standalone — called by API route directly) ────────────────

async def score_quiz(
    questions: list[dict],
    user_answers: list[dict],
) -> dict[str, Any]:
    """
    Score submitted answers against the stored questions.

    For MCQ: performs exact-match scoring first (no LLM needed).
    Then calls Gemini for weak area analysis and recommendations.

    This two-step approach:
      - Makes scoring fast (exact match is instant)
      - Makes weak area detection intelligent (Gemini clusters topics)
      - Reduces tokens (only send scoring analysis, not full generation)
    """
    if not questions or not user_answers:
        return _empty_score_result()

    # ── Step 1: Exact match scoring (instant, no LLM) ─────────────────────────
    answer_map = {
        (a.get("question_id") or a.get("id")): str(a.get("answer", "")).strip().upper()
        for a in user_answers
    }

    correct_count = 0
    quick_results = []
    for q in questions:
        qid       = q.get("id", 0)
        correct   = str(q.get("correct_answer", "")).strip().upper()
        user_ans  = answer_map.get(qid, "")
        is_correct = (user_ans == correct)
        if is_correct:
            correct_count += 1
        quick_results.append({
            "question_id":   qid,
            "user_answer":   user_ans,
            "correct_answer": correct,
            "is_correct":    is_correct,
            "topic_area":    q.get("topic_area", "General"),
        })

    score_percent = round((correct_count / len(questions)) * 100) if questions else 0

    # ── Step 2: LLM weak area analysis ────────────────────────────────────────
    try:
        llm = get_gemini_flash()
        response = await llm.ainvoke([
            SystemMessage(content=SCORING_SYSTEM),
            HumanMessage(content=build_scoring_prompt(questions, user_answers)),
        ])
        analysis = _parse_json(response.content)
    except Exception as e:
        logger.error(f"[QuizAgent] Scoring LLM call failed: {e}")
        # Fall back to basic scoring without AI analysis
        analysis = _basic_score_analysis(quick_results, score_percent)

    # Merge our exact-match results with LLM's weak area analysis
    return _enrich_score_result(analysis, quick_results, score_percent, correct_count, len(questions))


# ── Parsing ────────────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict[str, Any]:
    text     = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    start    = text.find("{")
    end      = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object in response")
    json_str = re.sub(r",\s*([}\]])", r"\1", text[start:end])
    return json.loads(json_str)


def _enrich_quiz_output(
    raw: dict[str, Any],
    topic: str,
    difficulty: str,
    quiz_type: str,
) -> dict[str, Any]:
    """Normalise quiz output and guarantee all required keys exist."""
    questions = raw.get("questions", [])
    if not isinstance(questions, list):
        questions = []

    # Ensure sequential IDs
    for i, q in enumerate(questions, start=1):
        if isinstance(q, dict) and "id" not in q:
            q["id"] = i

    return {
        "quiz_type":           quiz_type,
        "topic":               raw.get("topic", topic),
        "difficulty":          raw.get("difficulty", difficulty),
        "questions":           questions,
        "total_questions":     len(questions),
        "topic_areas_covered": raw.get("topic_areas_covered", []),
        # Populated after scoring
        "score_percent":       None,
        "correct_answers":     None,
        "weak_areas":          [],
        "strong_areas":        [],
        "analysis_source": "ai",
    }


def _enrich_score_result(
    analysis: dict,
    quick_results: list[dict],
    score_percent: int,
    correct_count: int,
    total: int,
) -> dict[str, Any]:
    """Merge exact-match results with LLM analysis into final score dict."""

    def safe_list(val, default=None):
        return val if isinstance(val, list) else (default or [])

    grade = _score_to_grade(score_percent)

    return {
        "total_questions":          total,
        "correct_answers":          correct_count,
        "score_percent":            score_percent,
        "grade":                    analysis.get("grade", grade),
        "question_results":         quick_results,     # exact-match results (fast)
        "weak_areas":               safe_list(analysis.get("weak_areas"), []),
        "strong_areas":             safe_list(analysis.get("strong_areas"), []),
        "topic_performance":        analysis.get("topic_performance", {}),
        "improvement_recommendations": safe_list(analysis.get("improvement_recommendations"), []),
        "next_quiz_focus":          safe_list(analysis.get("next_quiz_focus"), []),
        "encouragement":            analysis.get("encouragement", f"You scored {score_percent}%!"),
    }


def _basic_score_analysis(quick_results: list[dict], score_percent: int) -> dict:
    """Fallback when LLM scoring call fails — derive weak areas from results."""
    from collections import Counter
    wrong_topics = [r["topic_area"] for r in quick_results if not r["is_correct"]]
    topic_counts = Counter(wrong_topics)
    weak_areas   = [topic for topic, _ in topic_counts.most_common(3)]

    right_topics = [r["topic_area"] for r in quick_results if r["is_correct"]]
    strong_areas = list({t for t in right_topics if t not in weak_areas})[:3]

    return {
        "weak_areas":   weak_areas,
        "strong_areas": strong_areas,
        "encouragement": f"You scored {score_percent}%!",
        "improvement_recommendations": [f"Review {t}" for t in weak_areas],
        "next_quiz_focus": weak_areas,
        "topic_performance": {},
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _resolve_topic(state: CareerCopilotState) -> str:
    """Auto-select a quiz topic from context if not explicitly provided."""
    if state.get("quiz_topic"):
        return state["quiz_topic"]

    # Use skill gap priority order
    skill_gap = state.get("skill_gap_analysis", {})
    priority  = skill_gap.get("priority_order", [])
    if priority and isinstance(priority[0], str):
        logger.info(f"[QuizAgent] Auto-selected topic from skill gaps: {priority[0]}")
        return priority[0]

    # Use previous quiz's recommended focus
    prev_quiz = state.get("quiz_output", {})
    next_focus = prev_quiz.get("next_quiz_focus", [])
    if next_focus:
        return next_focus[0]

    return "Computer Science Fundamentals"


def _score_to_grade(score: int) -> str:
    if score >= 90: return "excellent"
    if score >= 75: return "good"
    if score >= 60: return "satisfactory"
    return "needs_improvement"


def _empty_output(topic: str, difficulty: str, reason: str) -> dict[str, Any]:
    return {
        "quiz_type": "mcq", "topic": topic, "difficulty": difficulty,
        "questions": [], "total_questions": 0, "topic_areas_covered": [],
        "score_percent": None, "correct_answers": None,
        "weak_areas": [], "strong_areas": [],
        "analysis_source": "error", "error_reason": reason,
    }


def _empty_score_result() -> dict[str, Any]:
    return {
        "total_questions": 0, "correct_answers": 0, "score_percent": 0,
        "grade": "needs_improvement", "question_results": [],
        "weak_areas": [], "strong_areas": [], "topic_performance": {},
        "improvement_recommendations": [], "next_quiz_focus": [], "encouragement": "",
    }
