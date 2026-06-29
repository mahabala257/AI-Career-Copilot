"""
app/agents/personal/project_recommendation_agent.py
─────────────────────────────────────────────────────
Project Recommendation Agent — LangGraph node implementation.

Reads from state:
  target_role, experience_level, time_available_weeks
  resume_analysis (extracted_skills, existing projects from raw_text)
  skill_gap_analysis (missing_skills for gap-closing projects)
  rag_context (injected by enrich_state_with_rag)

Writes to state:
  project_recommendations_output
  agents_called — appends AgentName.PROJECT_RECOMMEND
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.personal.project_recommendation_prompts import (
    PROJECT_SYSTEM,
    build_project_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def project_recommendation_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    LangGraph node: Project Recommendation Agent.

    Cross-references resume skills and skill gaps to recommend
    the highest-impact projects for the user's target role.
    """
    logger.info(
        f"[ProjectAgent] Starting | user={state.get('user_id')} | "
        f"role={state.get('target_role')} | level={state.get('experience_level')}"
    )

    # ── Extract inputs from state ──────────────────────────────────────────────
    target_role          = state.get("target_role", "Software Engineer")
    experience_level     = state.get("experience_level", "fresher")
    time_available_weeks = state.get("time_available_weeks", 4)

    # Pull skills from resume analysis if available
    resume_analysis  = state.get("resume_analysis", {})
    current_skills   = resume_analysis.get("extracted_skills", [])

    # Pull missing skills from skill gap analysis if available
    skill_gap        = state.get("skill_gap_analysis", {})
    missing_skills   = skill_gap.get("priority_order", [])

    # Try to extract existing project names from resume (heuristic)
    existing_projects = _extract_projects_from_resume(
        resume_analysis.get("raw_text", ""),
        resume_analysis.get("strengths", []),
    )

    # ── RAG enrichment ─────────────────────────────────────────────────────────
    rag_update  = await enrich_state_with_rag(state, AgentName.PROJECT_RECOMMEND)
    rag_context = rag_update.get("rag_context", [])
    logger.info(f"[ProjectAgent] RAG retrieved {len(rag_context)} chunks")

    # ── Build and call Gemini ──────────────────────────────────────────────────
    try:
        llm = get_gemini_flash()
        human_prompt = build_project_prompt(
            target_role=target_role,
            experience_level=experience_level,
            time_available_weeks=time_available_weeks,
            current_skills=current_skills,
            missing_skills=missing_skills,
            existing_projects=existing_projects,
            rag_context=rag_context,
        )

        response = await llm.ainvoke([
            SystemMessage(content=PROJECT_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        raw    = response.content
        result = _parse_project_response(raw)

        logger.info(
            f"[ProjectAgent] Done | "
            f"{len(result.get('recommended_projects', []))} projects recommended | "
            f"portfolio_score={result.get('portfolio_score')} | "
            f"user={state.get('user_id')}"
        )

        return {
            "project_recommendations_output": result,
            "agents_called": [AgentName.PROJECT_RECOMMEND],
        }

    except Exception as e:
        logger.error(f"[ProjectAgent] Failed: {e}", exc_info=True)
        return {
            "project_recommendations_output": _fallback_output(str(e)),
            "error": str(e),
            "error_agent": AgentName.PROJECT_RECOMMEND,
            "agents_called": [AgentName.PROJECT_RECOMMEND],
        }


def _extract_projects_from_resume(raw_text: str, strengths: list[str]) -> list[str]:
    """
    Heuristic: look for project-sounding phrases in the resume text.
    This avoids recommending projects the user already built.
    """
    if not raw_text:
        return []

    projects = []
    # Common project section headers
    patterns = [
        r"(?i)(?:project|built|developed|created|implemented)[:\s]+([^\n]{10,60})",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, raw_text)
        projects.extend(m.strip() for m in matches[:5])

    return list(set(projects))[:5]


def _parse_project_response(raw: str) -> dict:
    """Parse Gemini JSON response."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]

    try:
        data = json.loads(cleaned)
        return _validate_project_output(data)
    except json.JSONDecodeError as e:
        logger.error(f"[ProjectAgent] JSON parse error: {e}")
        return _fallback_output("Could not parse recommendations. Please try again.")


def _validate_project_output(data: dict) -> dict:
    """Ensure required fields with safe defaults."""
    data.setdefault("portfolio_score", 30)
    data.setdefault("portfolio_assessment", "")
    data.setdefault("recommended_projects", [])
    data.setdefault("projects_to_avoid", [])
    data.setdefault("portfolio_target_score", 75)
    data.setdefault("portfolio_action_plan", [])

    # Validate each project has required fields
    for i, proj in enumerate(data["recommended_projects"]):
        proj.setdefault("rank", i + 1)
        proj.setdefault("title", f"Project {i + 1}")
        proj.setdefault("one_liner", "")
        proj.setdefault("description", "")
        proj.setdefault("why_this_impresses", "")
        proj.setdefault("skills_demonstrated", [])
        proj.setdefault("skills_learned", [])
        proj.setdefault("estimated_weeks", 2)
        proj.setdefault("difficulty", "intermediate")
        proj.setdefault("tech_stack", {})
        proj.setdefault("github_readme_sections", [])
        proj.setdefault("interview_talking_points", [])
        proj.setdefault("scale_question", "")
        proj.setdefault("demo_tip", "")

    return data


def _fallback_output(error_message: str) -> dict:
    return {
        "portfolio_score": 0,
        "portfolio_assessment": "",
        "recommended_projects": [],
        "projects_to_avoid": [],
        "portfolio_target_score": 0,
        "portfolio_action_plan": [],
        "error_reason": error_message,
    }
