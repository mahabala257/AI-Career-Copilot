"""
app/agents/personal/study_planner_agent.py
────────────────────────────────────────────
Production Study Planner Agent — replaces the stub in placeholders.py.

What makes this agent valuable
────────────────────────────────
Generic study plans are useless. "Study Python for 2 hours a day" tells a
student nothing actionable. This agent is valuable because it reads from
the outputs of EVERY previous agent in the same session:

  resume_analysis.extracted_skills     → knows what the user CAN do
  skill_gap_analysis.priority_order    → knows what to learn FIRST
  skill_gap_analysis.months_to_ready   → knows the URGENCY
  quiz_output.weak_areas               → knows what needs REINFORCEMENT
  available_hours                      → knows the USER'S CAPACITY

The resulting plan tells the user exactly:
  Monday: "Watch Docker crash course + run hello-world container" (not "learn Docker")

Plan types
───────────
  daily   → Single day, maximum detail per session block
  weekly  → 7 days with a theme, day-by-day progression
  monthly → 4 weeks with milestones and deliverables

State contract
───────────────
  Reads:
    state["plan_type"]          — "daily" | "weekly" | "monthly"
    state["available_hours"]    — float, hours per day
    state["target_role"]        — career goal
    state["skill_gap_analysis"] — priority_order, months_to_ready
    state["resume_analysis"]    — current skills, experience level
    state["quiz_output"]        — weak_areas for reinforcement

  Writes:
    state["study_plan_output"]  — full plan dict
    state["agents_called"]      — appends AgentName.STUDY_PLANNER
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.personal.study_planner_prompts import (
    DAILY_PLAN_SYSTEM,
    MONTHLY_PLAN_SYSTEM,
    WEEKLY_PLAN_SYSTEM,
    build_daily_plan_prompt,
    build_monthly_plan_prompt,
    build_weekly_plan_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def study_planner_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Study Planner Agent LangGraph node.
    Registered in graph.py as: graph.add_node(AgentName.STUDY_PLANNER, study_planner_agent_node)
    """
    user_id         = state.get("user_id", "unknown")
    target_role     = state.get("target_role", "Software Engineer")
    plan_type       = state.get("plan_type", "weekly")
    available_hours = float(state.get("available_hours", 2.0) or 2.0)

    # ── Extract context from previous agents ───────────────────────────────────
    context = _extract_planning_context(state)

    logger.info(
        f"[StudyPlannerAgent] Starting | user={user_id} | "
        f"plan_type={plan_type} | role={target_role} | "
        f"hours={available_hours} | priority_skills={context['priority_skills'][:3]}"
    )

    if not target_role:
        return {
            "study_plan_output": _empty_plan("daily", "No target role set."),
            "agents_called": [AgentName.STUDY_PLANNER],
            "error": "StudyPlannerAgent: target_role missing",
            "error_agent": AgentName.STUDY_PLANNER,
        }

    try:
        plan = await _generate_plan(
            plan_type=plan_type,
            target_role=target_role,
            available_hours=available_hours,
            context=context,
        )
    except Exception as e:
        logger.error(f"[StudyPlannerAgent] Failed: {e}", exc_info=True)
        return {
            "study_plan_output": _empty_plan(plan_type, str(e)[:120]),
            "agents_called": [AgentName.STUDY_PLANNER],
            "error": f"StudyPlannerAgent error: {str(e)[:200]}",
            "error_agent": AgentName.STUDY_PLANNER,
        }

    logger.info(f"[StudyPlannerAgent] Done | plan_type={plan_type}")

    return {
        "study_plan_output": plan,
        "agents_called": [AgentName.STUDY_PLANNER],
    }


# ── Plan generation ────────────────────────────────────────────────────────────

async def _generate_plan(
    plan_type: str,
    target_role: str,
    available_hours: float,
    context: dict,
) -> dict[str, Any]:
    """Dispatch to the right prompt builder and call Gemini."""
    llm = get_gemini_flash()

    priority_skills = context["priority_skills"]
    current_skills  = context["current_skills"]
    weak_areas      = context["weak_areas"]
    months_to_ready = context["months_to_ready"]

    if plan_type == "daily":
        # For daily plans, focus on the single most important skill gap
        focus_skill = priority_skills[0] if priority_skills else target_role
        system      = DAILY_PLAN_SYSTEM
        human       = build_daily_plan_prompt(
            target_role=target_role,
            skill_to_focus=focus_skill,
            available_hours=available_hours,
            current_skills=current_skills,
            weak_areas=weak_areas,
        )

    elif plan_type == "monthly":
        system = MONTHLY_PLAN_SYSTEM
        human  = build_monthly_plan_prompt(
            target_role=target_role,
            priority_skills=priority_skills,
            available_hours=available_hours,
            current_skills=current_skills,
            months_to_ready=months_to_ready,
        )

    else:  # weekly (default)
        system = WEEKLY_PLAN_SYSTEM
        human  = build_weekly_plan_prompt(
            target_role=target_role,
            priority_skills=priority_skills,
            available_hours=available_hours,
            current_skills=current_skills,
            weak_areas=weak_areas,
            months_to_ready=months_to_ready,
        )

    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=human),
    ])

    parsed   = _parse_json(response.content)
    enriched = _enrich_plan(parsed, plan_type, target_role, available_hours, context)
    return enriched


# ── Context extraction ─────────────────────────────────────────────────────────

def _extract_planning_context(state: CareerCopilotState) -> dict:
    """
    Pull all relevant data from previous agent outputs.
    Returns a clean dict the prompt builders can use directly.
    """
    # From Skill Gap Agent
    skill_gap        = state.get("skill_gap_analysis", {}) or {}
    priority_skills  = skill_gap.get("priority_order", [])
    months_to_ready  = int(skill_gap.get("months_to_job_ready", 6) or 6)

    # From Resume Agent
    resume           = state.get("resume_analysis", {}) or {}
    current_skills   = resume.get("extracted_skills", [])

    # Also pull from user profile in state
    profile_skills   = state.get("current_skills", []) or []
    # Merge, deduplicate
    merged_current   = list(dict.fromkeys(current_skills + profile_skills))

    # From Quiz Agent
    quiz             = state.get("quiz_output", {}) or {}
    weak_areas       = quiz.get("weak_areas", []) or []
    next_quiz_focus  = quiz.get("next_quiz_focus", []) or []

    # Combine weak areas from quiz and skill gaps for reinforcement
    all_weak = list(dict.fromkeys(weak_areas + next_quiz_focus))[:5]

    return {
        "priority_skills":  [s for s in priority_skills if isinstance(s, str)][:8],
        "current_skills":   [s for s in merged_current  if isinstance(s, str)][:10],
        "weak_areas":       [s for s in all_weak         if isinstance(s, str)],
        "months_to_ready":  months_to_ready,
    }


# ── Parsing & enrichment ───────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict[str, Any]:
    text     = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    start    = text.find("{")
    end      = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object in response")
    json_str = re.sub(r",\s*([}\]])", r"\1", text[start:end])
    return json.loads(json_str)


def _enrich_plan(
    raw: dict[str, Any],
    plan_type: str,
    target_role: str,
    available_hours: float,
    context: dict,
) -> dict[str, Any]:
    """Add metadata and normalise the plan structure."""

    def safe_list(v):
        return v if isinstance(v, list) else []

    base = {
        "plan_type":            plan_type,
        "target_role":          raw.get("target_role", target_role),
        "available_hours":      available_hours,
        "priority_skills_used": context["priority_skills"],
        "weak_areas_addressed": context["weak_areas"],
        "months_to_ready":      context["months_to_ready"],
        "analysis_source": "ai",
    }

    if plan_type == "daily":
        base.update({
            "focus_skill":     raw.get("focus_skill", ""),
            "sessions":        safe_list(raw.get("sessions")),
            "total_hours":     raw.get("total_study_hours", available_hours),
            "career_action":   raw.get("career_action", ""),
            "evening_review":  raw.get("evening_review", ""),
            "tomorrow_preview": raw.get("tomorrow_preview", ""),
            "motivational_note": raw.get("motivational_note", ""),
        })

    elif plan_type == "weekly":
        days = safe_list(raw.get("days"))
        # Ensure 7 days
        if len(days) < 7:
            days += [{"day": f"Day {i}", "tasks": [], "study_hours": available_hours}
                     for i in range(len(days) + 1, 8)]
        base.update({
            "week_theme":       raw.get("week_theme", ""),
            "days":             days,
            "week_project":     raw.get("week_project", ""),
            "weekly_milestone": raw.get("weekly_milestone", ""),
            "friday_career_task": raw.get("friday_career_task", ""),
            "weekend_review":   raw.get("weekend_review", ""),
            "target_skills":    safe_list(raw.get("target_skills_this_week")),
        })

    else:  # monthly
        weeks = safe_list(raw.get("weeks"))
        if len(weeks) < 4:
            weeks += [{"week_number": i + len(weeks) + 1, "key_tasks": []}
                      for i in range(4 - len(weeks))]
        base.update({
            "month_theme":      raw.get("month_theme", ""),
            "weeks":            weeks,
            "month_project":    raw.get("month_project", ""),
            "month_milestone":  raw.get("end_of_month_assessment", ""),
            "critical_skills":  safe_list(raw.get("critical_skills_covered")),
            "deferred_skills":  safe_list(raw.get("skills_deferred_to_next_month")),
        })

    return base


def _empty_plan(plan_type: str, reason: str) -> dict[str, Any]:
    return {
        "plan_type":       plan_type,
        "target_role":     "",
        "available_hours": 2.0,
        "sessions":        [] if plan_type == "daily" else None,
        "days":            [] if plan_type == "weekly" else None,
        "weeks":           [] if plan_type == "monthly" else None,
        "analysis_source": "error",
        "error_reason":    reason,
    }
