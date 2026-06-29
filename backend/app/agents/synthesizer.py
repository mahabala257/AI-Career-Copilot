"""
app/agents/synthesizer.py
──────────────────────────
The Response Synthesizer — the last node before END in the graph.

Why a dedicated synthesizer instead of having the last agent return the response?
  1. In multi-agent flows, multiple agents run and the user needs ONE coherent
     response — not 3 separate JSON blobs from 3 different agents
  2. The synthesizer can format the response differently based on what was called
     (a resume analysis response looks different from a study plan response)
  3. It's the right place to generate the recommendations list that feeds
     the Career Readiness Score Engine
  4. Error handling — if an agent failed, the synthesizer catches error state
     and returns a graceful degraded response instead of a crash

The synthesizer does NOT call an LLM (it's fast, deterministic, zero token cost).
It purely reorganizes the state data into a clean final_response dict.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.agents.state import AgentName, CareerCopilotState

logger = logging.getLogger(__name__)


async def synthesizer_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    Response Synthesizer LangGraph node.

    Collects all agent outputs from state, builds a unified final_response,
    and generates a top-level recommendations list.
    """
    logger.info(
        f"[Synthesizer] Building final response | "
        f"agents_called={state.get('agents_called', [])}"
    )

    agents_called = state.get("agents_called", [])
    error = state.get("error")
    error_agent = state.get("error_agent")

    # ── Collect agent outputs ──────────────────────────────────────────────────
    agent_outputs: dict[str, Any] = {}

    if state.get("resume_analysis"):
        agent_outputs[AgentName.RESUME] = state["resume_analysis"]

    if state.get("skill_gap_analysis"):
        agent_outputs[AgentName.SKILL_GAP] = state["skill_gap_analysis"]

    if state.get("interview_output"):
        agent_outputs[AgentName.INTERVIEW] = state["interview_output"]

    if state.get("quiz_output"):
        agent_outputs[AgentName.QUIZ] = state["quiz_output"]

    if state.get("study_plan_output"):
        agent_outputs[AgentName.STUDY_PLANNER] = state["study_plan_output"]

    # ── Build summary message ──────────────────────────────────────────────────
    summary = _build_summary(state, agent_outputs, error)

    # ── Extract recommendations ────────────────────────────────────────────────
    # Pull the top recommendations from whichever agents ran.
    # These feed the Career Readiness Score Engine.
    recommendations = _extract_recommendations(agent_outputs)

    # ── Build final response ───────────────────────────────────────────────────
    final_response = {
        "summary": summary,
        "agents_called": [a for a in agents_called if a != AgentName.SUPERVISOR],
        "agent_outputs": agent_outputs,
        "recommendations": recommendations,
        "has_error": bool(error),
        "error_details": {
            "message": error,
            "agent": error_agent,
        } if error else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # Intent context for the frontend to display the right UI component
        "primary_output_type": _determine_primary_output_type(agents_called),
    }

    logger.info(f"[Synthesizer] Final response built. Output type: {final_response['primary_output_type']}")

    return {"final_response": final_response}


def _build_summary(
    state: CareerCopilotState,
    agent_outputs: dict,
    error: str | None,
) -> str:
    """
    Build a human-readable summary of what was accomplished.
    This is the text shown to the user at the top of the response.
    """
    if error and not agent_outputs:
        return (
            "I encountered an issue processing your request. "
            "Please try again or rephrase your question."
        )

    user_message = state.get("user_message", "")
    agents = list(agent_outputs.keys())

    if not agents:
        return "I received your request but no agents were able to process it. Please try again."

    summaries = []

    if AgentName.RESUME in agents:
        ats = agent_outputs[AgentName.RESUME].get("ats_score", "N/A")
        summaries.append(f"your resume has been analyzed (ATS score: {ats}/100)")

    if AgentName.SKILL_GAP in agents:
        missing = agent_outputs[AgentName.SKILL_GAP].get("missing_skills", [])
        count = len(missing)
        summaries.append(f"{count} skill gap{'s' if count != 1 else ''} identified")

    if AgentName.INTERVIEW in agents:
        questions = agent_outputs[AgentName.INTERVIEW].get("questions", [])
        i_type = agent_outputs[AgentName.INTERVIEW].get("session_type", "interview")
        summaries.append(f"{len(questions)} {i_type} questions generated")

    if AgentName.QUIZ in agents:
        questions = agent_outputs[AgentName.QUIZ].get("questions", [])
        topic = agent_outputs[AgentName.QUIZ].get("topic", "")
        summaries.append(f"a {len(questions)}-question quiz on {topic} is ready")

    if AgentName.STUDY_PLANNER in agents:
        plan_type = agent_outputs[AgentName.STUDY_PLANNER].get("plan_type", "study")
        summaries.append(f"a {plan_type} study plan has been created")

    if summaries:
        return "Here's what I've prepared for you: " + ", and ".join(summaries) + "."
    return "Your request has been processed."


def _extract_recommendations(agent_outputs: dict) -> list[str]:
    """
    Pull top action items from agent outputs for the dashboard widget.
    Maximum 5 recommendations to avoid overwhelming the user.
    """
    recommendations = []

    # From Resume Agent
    if AgentName.RESUME in agent_outputs:
        resume = agent_outputs[AgentName.RESUME]
        suggestions = resume.get("suggestions", [])
        recommendations.extend(suggestions[:2])

        missing = resume.get("missing_skills", [])
        if missing:
            recommendations.append(f"Learn {missing[0]} to improve ATS score")

    # From Skill Gap Agent
    if AgentName.SKILL_GAP in agent_outputs:
        skill_gap = agent_outputs[AgentName.SKILL_GAP]
        priority_order = skill_gap.get("priority_order", [])
        if priority_order:
            recommendations.append(f"Priority learning: {priority_order[0]}")

    # From Quiz Agent
    if AgentName.QUIZ in agent_outputs:
        quiz = agent_outputs[AgentName.QUIZ]
        weak_areas = quiz.get("weak_areas", [])
        if weak_areas:
            recommendations.append(f"Review weak area: {weak_areas[0]}")

    # Deduplicate and limit to 5
    seen = set()
    unique_recommendations = []
    for r in recommendations:
        if r not in seen and r:
            seen.add(r)
            unique_recommendations.append(r)
        if len(unique_recommendations) >= 5:
            break

    return unique_recommendations


def _determine_primary_output_type(agents_called: list[str]) -> str:
    """
    Tell the frontend which UI component to render primarily.
    The frontend uses this to decide which panel to show first.
    """
    # Priority order — if multiple agents ran, show the most interactive output
    priority = [
        AgentName.QUIZ,
        AgentName.INTERVIEW,
        AgentName.RESUME,
        AgentName.STUDY_PLANNER,
        AgentName.SKILL_GAP,
    ]
    for agent in priority:
        if agent in agents_called:
            return agent

    return "general"
