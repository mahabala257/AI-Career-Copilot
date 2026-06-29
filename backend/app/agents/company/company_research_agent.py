"""
app/agents/company/company_research_agent.py
─────────────────────────────────────────────
Company Research Agent — LangGraph node implementation.

Reads from state:
  company_name, target_role
  resume_analysis (for current skills → alignment score)
  rag_context (injected by enrich_state_with_rag)

Writes to state:
  company_research_output
  agents_called — appends AgentName.COMPANY_RESEARCH
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.company.company_research_prompts import (
    COMPANY_RESEARCH_SYSTEM,
    build_company_research_prompt,
)
from app.agents.state import AgentName, CareerCopilotState
from app.llm.gemini_client import get_gemini_flash
from app.rag.rag_pipeline import enrich_state_with_rag

logger = logging.getLogger(__name__)


async def company_research_agent_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    LangGraph node: Company Research Agent.
    Produces a complete preparation guide for a target company:
    tech stack, interview style, culture, known question types,
    skill alignment, and week-by-week prep strategy.
    """
    company_name    = state.get("company_name", "").strip()
    target_role     = state.get("target_role", "Software Engineer")
    work_mode       = state.get("work_mode", "Any") or "Any"
    employment_type = state.get("employment_type", "Any") or "Any"
    resume          = state.get("resume_analysis", {})
    skills          = resume.get("extracted_skills", [])

    logger.info(
        f"[CompanyAgent] Starting | user={state.get('user_id')} | "
        f"company={company_name} | role={target_role}"
    )

    if not company_name:
        logger.warning("[CompanyAgent] No company_name in state")
        return {
            "company_research_output": _fallback_output(
                "No company name was provided. Please specify which company to research."
            ),
            "agents_called": [AgentName.COMPANY_RESEARCH],
        }

    # ── RAG enrichment ─────────────────────────────────────────────────────────
    rag_update  = await enrich_state_with_rag(state, AgentName.COMPANY_RESEARCH)
    rag_context = rag_update.get("rag_context", [])
    logger.info(f"[CompanyAgent] RAG: {len(rag_context)} chunks")

    # ── Call Gemini ────────────────────────────────────────────────────────────
    try:
        llm = get_gemini_flash()
        human_prompt = build_company_research_prompt(
            company_name=company_name,
            target_role=target_role,
            current_skills=skills,
            rag_context=rag_context,
            work_mode=work_mode,
            employment_type=employment_type,
        )

        response = await llm.ainvoke([
            SystemMessage(content=COMPANY_RESEARCH_SYSTEM),
            HumanMessage(content=human_prompt),
        ])

        result = _parse_response(response.content)

        logger.info(
            f"[CompanyAgent] Done | company={company_name} | "
            f"alignment={result.get('skill_alignment', {}).get('alignment_score')} | "
            f"user={state.get('user_id')}"
        )
        return {
            "company_research_output": result,
            "agents_called": [AgentName.COMPANY_RESEARCH],
        }

    except Exception as e:
        logger.error(f"[CompanyAgent] Failed: {e}", exc_info=True)
        return {
            "company_research_output": _fallback_output(str(e)),
            "error": str(e),
            "error_agent": AgentName.COMPANY_RESEARCH,
            "agents_called": [AgentName.COMPANY_RESEARCH],
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
        logger.error(f"[CompanyAgent] JSON parse error: {e}")
        return _fallback_output("Could not parse company research response. Please try again.")


def _validate(data: dict) -> dict:
    data.setdefault("company_name",        "")
    data.setdefault("company_type",        "product")
    data.setdefault("overview",            "")
    data.setdefault("tech_stack",          [])
    data.setdefault("engineering_culture", "")
    data.setdefault("interview_style",     "")
    data.setdefault("interview_rounds",    [])
    data.setdefault("culture_values",      [])
    data.setdefault("known_question_types",[])
    data.setdefault("skill_alignment",     {"matching_skills": [], "missing_skills": [], "alignment_score": 50})
    data.setdefault("prep_strategy",       [])
    data.setdefault("typical_timeline",    "")
    data.setdefault("salary_range",        "")
    data.setdefault("pros",                [])
    data.setdefault("cons",                [])
    data.setdefault("glassdoor_rating",    None)
    data.setdefault("application_tips",    [])
    data.setdefault("typical_openings",    [])
    return data


def _fallback_output(error_message: str) -> dict:
    return {
        "company_name": "", "company_type": "", "overview": "",
        "tech_stack": [], "engineering_culture": "", "interview_style": "",
        "interview_rounds": [], "culture_values": [], "known_question_types": [],
        "skill_alignment": {"matching_skills": [], "missing_skills": [], "alignment_score": 0},
        "prep_strategy": [], "typical_timeline": "", "salary_range": "",
        "pros": [], "cons": [], "glassdoor_rating": None, "application_tips": [],
        "typical_openings": [], "error_reason": error_message,
    }
