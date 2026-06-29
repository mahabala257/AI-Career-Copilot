"""
tests/test_phase3.py
─────────────────────
Tests for Phase 3 agents:
  - Company Research Agent
  - Internship Research Agent
  - Wellness & Motivation Agent
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


def make_state(**overrides) -> dict[str, Any]:
    base = {
        "user_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "user_message": "test",
        "target_role": "AI Engineer",
        "resume_text": "",
        "resume_analysis": {
            "extracted_skills": ["Python", "FastAPI", "SQL"],
            "strengths": ["Built a recommendation system"],
            "raw_text": "Python FastAPI developer.",
        },
        "skill_gap_analysis": {"priority_order": ["Docker", "Kubernetes"]},
        "company_name": "Google",
        "education_level": "B.Tech 3rd year",
        "college_tier": "Tier 2",
        "available_from": "May 2025",
        "mood_message": "",
        "next_agent": "", "routing_reasoning": "", "agent_queue": [],
        "agents_called": [], "is_multi_agent": False, "rag_context": [],
        "error": None, "error_agent": None,
        "company_research_output": {}, "internship_research_output": {},
        "wellness_output": {}, "final_response": {},
    }
    base.update(overrides)
    return base


COMPANY_AGENT_RESPONSE = {
    "company_name": "Google", "company_type": "product",
    "overview": "Google builds products used by billions.",
    "tech_stack": ["Go", "Python", "Kubernetes"],
    "engineering_culture": "Data-driven, OKR-based.",
    "interview_style": "5-7 rounds over 4-6 weeks.",
    "interview_rounds": [{"round": "Phone Screen", "focus": "DSA", "tips": "Practice LeetCode medium"}],
    "culture_values": ["Innovation", "Data-driven decisions"],
    "known_question_types": [{"type": "system_design", "example": "Design a URL shortener"}],
    "skill_alignment": {"matching_skills": ["Python"], "missing_skills": ["Go", "Kubernetes"], "alignment_score": 55},
    "prep_strategy": [{"week": 1, "focus": "DSA", "daily_hours": 2, "resources": ["LeetCode"]}],
    "typical_timeline": "4-6 weeks", "salary_range": "₹25-45 LPA",
    "pros": ["Great compensation"], "cons": ["High pressure"],
    "glassdoor_rating": 4.3, "application_tips": ["Apply via referral"],
}

INTERNSHIP_AGENT_RESPONSE = {
    "student_profile_summary": "3rd year B.Tech student targeting SDE internships.",
    "recommended_companies": [
        {
            "company": "Razorpay", "program_name": "SDE Intern",
            "company_type": "startup", "application_window": "October-December",
            "stipend_range": "₹50,000-80,000/month", "duration": "2 months",
            "selection_process": ["Online test", "2 technical rounds"],
            "ppo_likelihood": "High", "required_skills": ["Python", "APIs"],
            "nice_to_have": ["Go"], "college_tier_accepted": "all",
            "application_platform": "Razorpay Careers", "fit_score": 72,
        }
    ],
    "application_timeline": {"3_months_before": "Build projects", "1_month_before": "Apply"},
    "cover_letter_outline": {"opening": "Intro", "body": "Why me", "closing": "Thanks"},
    "skill_gaps_for_internships": ["System Design"],
    "preparation_priorities": [{"priority": 1, "skill": "DSA", "why": "Core requirement", "resource": "LeetCode"}],
    "top_platforms": ["LinkedIn", "Internshala"],
    "resume_tips_for_internships": ["Highlight projects"],
    "networking_tips": ["Connect with alumni"],
    "common_mistakes": ["Applying too late"],
}

WELLNESS_AGENT_RESPONSE = {
    "emotional_validation": "Feeling discouraged after rejections is completely valid.",
    "reframe": "Rejection is calibration data, not a verdict on your ability.",
    "next_single_action": "Review one interview question from your last attempt for 20 minutes today.",
    "progress_acknowledgment": "You've completed several practice sessions this week.",
    "burnout_risk": {"level": "medium", "signals": ["3 failed attempts in a row"], "recommendation": "Take a 1-day break."},
    "motivational_quote": "It does not matter how slowly you go as long as you do not stop.",
    "weekly_reflection_prompt": "What's one thing you learned this week?",
    "adjusted_study_plan": {"recommendation": "Reduce daily hours by 30%", "reason": "Prevent burnout"},
    "career_perspective": "Most engineers face many rejections before landing a role.",
    "professional_help_note": None, "professional_help_flag": False, "crisis_resources": None,
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. UNIT TESTS — Prompts
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanyPrompts:
    def test_build_prompt_includes_company_and_role(self):
        from app.agents.company.company_research_prompts import build_company_research_prompt
        prompt = build_company_research_prompt(
            company_name="Google", target_role="SDE-1",
            current_skills=["Python"], rag_context=[],
        )
        assert "Google" in prompt
        assert "SDE-1" in prompt

    def test_system_prompt_requires_json(self):
        from app.agents.company.company_research_prompts import COMPANY_RESEARCH_SYSTEM
        assert "JSON" in COMPANY_RESEARCH_SYSTEM
        assert "skill_alignment" in COMPANY_RESEARCH_SYSTEM


class TestInternshipPrompts:
    def test_build_prompt_includes_tier_and_level(self):
        from app.agents.company.internship_research_prompts import build_internship_research_prompt
        prompt = build_internship_research_prompt(
            target_role="SDE Intern", education_level="B.Tech 3rd year",
            college_tier="Tier 2", available_from="May 2025",
            current_skills=["Python"], missing_skills=["Go"], rag_context=[],
        )
        assert "Tier 2" in prompt
        assert "B.Tech 3rd year" in prompt

    def test_system_prompt_requires_realistic_recommendations(self):
        from app.agents.company.internship_research_prompts import INTERNSHIP_RESEARCH_SYSTEM
        assert "REALISTIC" in INTERNSHIP_RESEARCH_SYSTEM


class TestWellnessPrompts:
    def test_crisis_detection_positive(self):
        from app.agents.personal.wellness_prompts import detect_crisis
        assert detect_crisis("I want to kill myself") is True
        assert detect_crisis("I feel like ending my life") is True

    def test_crisis_detection_negative(self):
        from app.agents.personal.wellness_prompts import detect_crisis
        assert detect_crisis("I failed my interview and feel sad") is False
        assert detect_crisis("I'm stressed about my job search") is False

    def test_crisis_response_has_resources(self):
        from app.agents.personal.wellness_prompts import CRISIS_RESPONSE
        assert CRISIS_RESPONSE["professional_help_flag"] is True
        assert CRISIS_RESPONSE["crisis_resources"] is not None
        assert "india" in CRISIS_RESPONSE["crisis_resources"]

    def test_system_prompt_has_safety_rules(self):
        from app.agents.personal.wellness_prompts import WELLNESS_SYSTEM
        assert "MANDATORY SAFETY RULES" in WELLNESS_SYSTEM
        assert "professional_help_flag" in WELLNESS_SYSTEM

    def test_build_wellness_prompt_includes_context(self):
        from app.agents.personal.wellness_prompts import build_wellness_prompt
        prompt = build_wellness_prompt(
            mood_message="I feel discouraged",
            target_role="AI Engineer", career_score=65,
            sessions_this_week=3, recent_failures=2, rag_context=[],
        )
        assert "I feel discouraged" in prompt
        assert "65/100" in prompt


# ─────────────────────────────────────────────────────────────────────────────
# 2. AGENT NODE TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestCompanyAgentNode:
    async def test_node_returns_research(self):
        from app.agents.company.company_research_agent import company_research_agent_node
        mock_response = MagicMock()
        mock_response.content = json.dumps(COMPANY_AGENT_RESPONSE)

        with patch("app.agents.company.company_research_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.company.company_research_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm
                result = await company_research_agent_node(make_state())

        assert result["company_research_output"]["company_name"] == "Google"
        assert "company_research_agent" in result["agents_called"]

    async def test_node_fallback_when_no_company(self):
        from app.agents.company.company_research_agent import company_research_agent_node
        state = make_state(company_name="")
        result = await company_research_agent_node(state)
        assert "error_reason" in result["company_research_output"]

    async def test_node_handles_llm_exception(self):
        from app.agents.company.company_research_agent import company_research_agent_node
        with patch("app.agents.company.company_research_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.company.company_research_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("API error"))
                mock_llm_fn.return_value = mock_llm
                result = await company_research_agent_node(make_state())
        assert "error" in result


@pytest.mark.asyncio
class TestInternshipAgentNode:
    async def test_node_returns_recommendations(self):
        from app.agents.company.internship_research_agent import internship_research_agent_node
        mock_response = MagicMock()
        mock_response.content = json.dumps(INTERNSHIP_AGENT_RESPONSE)

        with patch("app.agents.company.internship_research_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.company.internship_research_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm
                result = await internship_research_agent_node(make_state())

        out = result["internship_research_output"]
        assert len(out["recommended_companies"]) == 1
        assert out["recommended_companies"][0]["company"] == "Razorpay"
        assert "internship_research_agent" in result["agents_called"]

    async def test_node_handles_llm_failure(self):
        from app.agents.company.internship_research_agent import internship_research_agent_node
        with patch("app.agents.company.internship_research_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.company.internship_research_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("timeout"))
                mock_llm_fn.return_value = mock_llm
                result = await internship_research_agent_node(make_state())
        assert result["internship_research_output"]["recommended_companies"] == []
        assert "error" in result


@pytest.mark.asyncio
class TestWellnessAgentNode:
    async def test_node_returns_supportive_response(self):
        from app.agents.personal.wellness_agent import wellness_agent_node
        mock_response = MagicMock()
        mock_response.content = json.dumps(WELLNESS_AGENT_RESPONSE)

        with patch("app.agents.personal.wellness_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.wellness_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm
                state = make_state(mood_message="I failed 3 interviews and feel discouraged")
                result = await wellness_agent_node(state)

        out = result["wellness_output"]
        assert out["burnout_risk"]["level"] == "medium"
        assert out["professional_help_flag"] is False
        assert "wellness_agent" in result["agents_called"]

    async def test_node_detects_crisis_without_llm_call(self):
        """CRITICAL: crisis messages must never reach the LLM — immediate response only."""
        from app.agents.personal.wellness_agent import wellness_agent_node

        with patch("app.agents.personal.wellness_agent.get_gemini_flash") as mock_llm_fn:
            state = make_state(mood_message="I want to kill myself, I can't do this anymore")
            result = await wellness_agent_node(state)

            # LLM must NEVER be called for crisis messages
            mock_llm_fn.assert_not_called()

        assert result["wellness_output"]["professional_help_flag"] is True
        assert result["wellness_output"]["crisis_resources"] is not None
        assert "wellness_agent" in result["agents_called"]

    async def test_node_handles_empty_message(self):
        from app.agents.personal.wellness_agent import wellness_agent_node
        state = make_state(mood_message="")
        result = await wellness_agent_node(state)
        assert "wellness_output" in result

    async def test_node_handles_llm_exception(self):
        from app.agents.personal.wellness_agent import wellness_agent_node
        with patch("app.agents.personal.wellness_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.wellness_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("API down"))
                mock_llm_fn.return_value = mock_llm
                state = make_state(mood_message="I'm feeling a bit stressed about applications")
                result = await wellness_agent_node(state)
        assert "error" in result


# ─────────────────────────────────────────────────────────────────────────────
# 3. API ROUTE TESTS
# ─────────────────────────────────────────────────────────────────────────────

def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.target_role = "AI Engineer"
    user.is_active = True
    return user


@pytest.mark.asyncio
class TestCompanyRoutes:
    async def test_research_returns_200(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        service_response = {
            "research_id": str(uuid.uuid4()), "company_name": "Google",
            "target_role": "SDE-1", "result": COMPANY_AGENT_RESPONSE,
            "agent_error": None, "researched_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("app.api.routes.company.run_company_research",
                   new=AsyncMock(return_value=service_response)):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/api/company/research", json={
                    "company_name": "Google", "target_role": "SDE-1",
                })

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["result"]["skill_alignment"]["alignment_score"] == 55
        app.dependency_overrides.clear()

    async def test_research_requires_company_name(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post("/api/company/research", json={})

        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestInternshipRoutes:
    async def test_research_returns_200(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        service_response = {
            "research_id": str(uuid.uuid4()), "target_role": "SDE Intern",
            "education_level": "B.Tech 3rd year", "result": INTERNSHIP_AGENT_RESPONSE,
            "agent_error": None, "researched_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("app.api.routes.internship.run_internship_research",
                   new=AsyncMock(return_value=service_response)):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/api/internship/research", json={
                    "target_role": "SDE Intern", "education_level": "B.Tech 3rd year",
                    "college_tier": "Tier 2",
                })

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["result"]["recommended_companies"]) == 1
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestWellnessRoutes:
    async def test_checkin_returns_200(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        service_response = {
            "checkin_id": str(uuid.uuid4()), "result": WELLNESS_AGENT_RESPONSE,
            "agent_error": None, "checked_in_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("app.api.routes.wellness.run_wellness_checkin",
                   new=AsyncMock(return_value=service_response)):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/api/wellness/checkin", json={
                    "mood_message": "I'm feeling discouraged after rejections",
                })

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["result"]["burnout_risk"]["level"] == "medium"
        assert data["result"]["professional_help_flag"] is False
        app.dependency_overrides.clear()

    async def test_checkin_requires_message(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post("/api/wellness/checkin", json={"mood_message": ""})

        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# 4. STATE INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestPhase3StateFields:
    def test_create_initial_state_has_phase3_fields(self):
        from app.agents.state import create_initial_state
        state = create_initial_state(
            user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
            user_message="Research Google", company_name="Google",
        )
        assert state["company_name"] == "Google"
        assert state["company_research_output"] == {}
        assert state["internship_research_output"] == {}
        assert state["wellness_output"] == {}

    def test_agent_names_include_phase3(self):
        from app.agents.state import AgentName
        assert AgentName.COMPANY_RESEARCH == "company_research_agent"
        assert AgentName.INTERNSHIP_RESEARCH == "internship_research_agent"
        assert AgentName.WELLNESS == "wellness_agent"
        assert AgentName.COMPANY_RESEARCH in AgentName.ALL_AGENTS
        assert AgentName.WELLNESS in AgentName.ALL_AGENTS

    def test_all_agents_includes_all_three_phases(self):
        from app.agents.state import AgentName
        expected = set(AgentName.PHASE_1_AGENTS) | set(AgentName.PHASE_2_AGENTS) | set(AgentName.PHASE_3_AGENTS)
        assert set(AgentName.ALL_AGENTS) == expected
        assert len(AgentName.ALL_AGENTS) == 11


# ─────────────────────────────────────────────────────────────────────────────
# 5. RAG RETRIEVER TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestPhase3Retrievers:
    async def test_retrieve_company_information(self):
        from app.rag.retriever import retrieve_company_information
        with patch("app.rag.retriever._query_collection",
                   new=AsyncMock(return_value=["Google interview process..."])) as mock_q:
            results = await retrieve_company_information("Google interview", company="Google")
        assert isinstance(results, list)
        assert mock_q.call_args[0][0] == "company_information"

    async def test_retrieve_internship_information(self):
        from app.rag.retriever import retrieve_internship_information
        with patch("app.rag.retriever._query_collection",
                   new=AsyncMock(return_value=["Microsoft internship program..."])) as mock_q:
            results = await retrieve_internship_information("internship programs")
        assert isinstance(results, list)
        assert mock_q.call_args[0][0] == "internship_information"

    async def test_retrieve_wellness_resources(self):
        from app.rag.retriever import retrieve_wellness_resources
        with patch("app.rag.retriever._query_collection",
                   new=AsyncMock(return_value=["Reframing rejection..."])) as mock_q:
            results = await retrieve_wellness_resources("rejection support", situation="rejection")
        assert isinstance(results, list)
        assert mock_q.call_args[0][0] == "wellness_resources"


# ─────────────────────────────────────────────────────────────────────────────
# 6. INTEGRATION TESTS — full request flow with graph routing
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestPhase3Integration:
    async def test_router_routes_to_company_research(self):
        from app.agents.router import route_after_agent
        from app.agents.state import AgentName

        state = make_state(agent_queue=[], agents_called=[AgentName.COMPANY_RESEARCH])
        result = route_after_agent(state)
        assert result == AgentName.SYNTHESIZER

    async def test_keyword_fallback_routes_wellness(self):
        from app.agents.supervisor import _keyword_fallback_routing
        from app.agents.state import AgentName

        result = _keyword_fallback_routing("I am feeling really stressed and want to give up")
        assert result == AgentName.WELLNESS

    async def test_keyword_fallback_routes_internship(self):
        from app.agents.supervisor import _keyword_fallback_routing
        from app.agents.state import AgentName

        result = _keyword_fallback_routing("looking for a summer internship opportunity")
        assert result == AgentName.INTERNSHIP_RESEARCH

    async def test_keyword_fallback_routes_company_research(self):
        from app.agents.supervisor import _keyword_fallback_routing
        from app.agents.state import AgentName

        result = _keyword_fallback_routing("tell me about google company culture")
        assert result == AgentName.COMPANY_RESEARCH
