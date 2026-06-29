"""
app/agents/company/internship_research_agent.py
─────────────────────────────────────────────────
Internship Research Agent — LangGraph node.

Reads from state:
  target_role, education_level, college_tier, available_from
  resume_analysis (current skills), skill_gap_analysis (missing skills)
  rag_context (injected by enrich_state_with_rag)

Writes to state:
  internship_research_output
  agents_called — appends AgentName.INTERNSHIP_RESEARCH
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.company.internship_research_prompts import (
    INTERNSHIP_RESEARCH_SYSTEM,
    build_internship_research_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def internship_research_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    LangGraph node: Internship Research Agent.
    Recommends realistic internship companies for the student's profile,
    application timeline, cover letter outline, and skill gap analysis.
    """
    target_role     = state.get("target_role", "Software Engineer Intern")
    education_level = state.get("education_level", "B.Tech 3rd year")
    college_tier    = state.get("college_tier", "Tier 2")
    available_from  = state.get("available_from", "")
    resume          = state.get("resume_analysis", {})
    skill_gap       = state.get("skill_gap_analysis", {})
    current_skills  = resume.get("extracted_skills", [])
    missing_skills  = skill_gap.get("priority_order", [])

    logger.info(
        f"[InternshipAgent] Starting | user={state.get('user_id')} | "
        f"role={target_role} | tier={college_tier}"
    )

    # ── RAG enrichment ─────────────────────────────────────────────────────────
    rag_update  = await enrich_state_with_rag(state, AgentName.INTERNSHIP_RESEARCH)
    rag_context = rag_update.get("rag_context", [])
    logger.info(f"[InternshipAgent] RAG: {len(rag_context)} chunks")

    try:
        llm = get_gemini_flash()
        human_prompt = build_internship_research_prompt(
            target_role=target_role,
            education_level=education_level,
            college_tier=college_tier,
            available_from=available_from,
            current_skills=current_skills,
            missing_skills=missing_skills,
            rag_context=rag_context,
        )

        response = await llm.ainvoke([
            SystemMessage(content=INTERNSHIP_RESEARCH_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        result = _parse_response(response.content)

        logger.info(
            f"[InternshipAgent] Done | "
            f"companies={len(result.get('recommended_companies', []))} | "
            f"user={state.get('user_id')}"
        )
        return {
            "internship_research_output": result,
            "agents_called": [AgentName.INTERNSHIP_RESEARCH],
        }

    except Exception as e:
        logger.error(f"[InternshipAgent] Failed: {e}", exc_info=True)
        return {
            "internship_research_output": _fallback_output(str(e)),
            "error": str(e),
            "error_agent": AgentName.INTERNSHIP_RESEARCH,
            "agents_called": [AgentName.INTERNSHIP_RESEARCH],
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
        logger.error(f"[InternshipAgent] JSON parse error: {e}")
        return _fallback_output("Could not parse internship research. Please try again.")


def _validate(data: dict) -> dict:
    data.setdefault("student_profile_summary",  "")
    data.setdefault("recommended_companies",     [])
    data.setdefault("application_timeline",      {})
    data.setdefault("cover_letter_outline",      {})
    data.setdefault("skill_gaps_for_internships",[])
    data.setdefault("preparation_priorities",    [])
    data.setdefault("top_platforms",             [])
    data.setdefault("resume_tips_for_internships",[])
    data.setdefault("networking_tips",           [])
    data.setdefault("common_mistakes",           [])

    for company in data["recommended_companies"]:
        company.setdefault("company",            "")
        company.setdefault("program_name",       "")
        company.setdefault("company_type",       "")
        company.setdefault("application_window", "")
        company.setdefault("stipend_range",      "")
        company.setdefault("duration",           "")
        company.setdefault("selection_process",  [])
        company.setdefault("ppo_likelihood",     "")
        company.setdefault("required_skills",    [])
        company.setdefault("nice_to_have",       [])
        company.setdefault("college_tier_accepted","all")
        company.setdefault("application_platform","")
        company.setdefault("fit_score",          50)

    return data


def _fallback_output(error_message: str) -> dict:
    return {
        "student_profile_summary": "",
        "recommended_companies": [], "application_timeline": {},
        "cover_letter_outline": {}, "skill_gaps_for_internships": [],
        "preparation_priorities": [], "top_platforms": [],
        "resume_tips_for_internships": [], "networking_tips": [],
        "common_mistakes": [], "error_reason": error_message,
    }
