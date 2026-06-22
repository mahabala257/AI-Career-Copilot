"""
tests/test_phase2.py
─────────────────────
Tests for Phase 2 agents:
  - LinkedIn Optimization Agent
  - Project Recommendation Agent
  - Spoken English Agent

Test levels:
  1. Unit  — prompt builders and response parsers (no network)
  2. Agent — agent node logic with mocked LLM and RAG
  3. API   — route handlers with mocked services and DB
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_state(**overrides) -> dict[str, Any]:
    """Build a minimal CareerCopilotState-compatible dict for agent tests."""
    base = {
        "user_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "user_message": "test",
        "target_role": "AI Engineer",
        "resume_text": "",
        "resume_analysis": {
            "extracted_skills": ["Python", "FastAPI", "SQL"],
            "strengths": ["Built a recommendation system"],
            "raw_text": "Python FastAPI developer with 2 years experience.",
        },
        "skill_gap_analysis": {
            "missing_skills": [{"skill": "Docker", "priority": "high"}],
            "priority_order": ["Docker", "Kubernetes"],
        },
        "linkedin_headline": "Python Developer | Open to opportunities",
        "linkedin_about": "I am a developer with 2 years of experience.",
        "linkedin_experience": "Worked on various Python projects.",
        "linkedin_skills": ["Python", "SQL"],
        "experience_level": "1-2 years",
        "time_available_weeks": 4,
        "spoken_text": "",
        "english_context_type": "interview_answer",
        "question_answered": "Tell me about yourself",
        "next_agent": "",
        "routing_reasoning": "",
        "agent_queue": [],
        "agents_called": [],
        "is_multi_agent": False,
        "rag_context": [],
        "error": None,
        "error_agent": None,
        "linkedin_output": {},
        "project_recommendations_output": {},
        "english_output": {},
        "final_response": {},
    }
    base.update(overrides)
    return base


LINKEDIN_AGENT_RESPONSE = {
    "current_score": 35,
    "optimized_score": 78,
    "score_breakdown": {"headline": 12, "about": 18, "experience": 20, "skills": 15, "completeness": 8},
    "sections": {
        "headline": {
            "current": "Python Developer | Open to opportunities",
            "optimized": "AI Engineer | Python · FastAPI · LLMs | Building production AI systems",
            "reasoning": "Role-first with searchable keywords.",
        },
        "about": {
            "current_summary": "I am a developer...",
            "optimized": "I build AI systems that ship to production and stay there.",
            "hook_score": 82,
            "reasoning": "Strong hook instead of generic opener.",
        },
        "experience_bullets": [
            {
                "original": "Worked on various Python projects.",
                "rewritten": "Engineered 5 FastAPI microservices handling 50K daily requests, reducing P95 latency by 40%.",
                "improvement": "Added metrics and strong action verb.",
            }
        ],
        "skills_reorder": {
            "recommended_top_3": ["Python", "FastAPI", "LLMs"],
            "skills_to_add": ["LangChain", "RAG"],
            "skills_to_remove": ["Microsoft Word"],
            "reasoning": "AI-relevant skills first for recruiter search.",
        },
    },
    "keyword_density": {
        "present_keywords": ["Python", "FastAPI"],
        "missing_high_value_keywords": ["LangChain", "RAG", "Vector Database"],
        "keyword_score": 45,
    },
    "top_3_changes": [
        "Rewrite headline with role-first format",
        "Replace generic About opener with a specific achievement hook",
        "Add LangChain and RAG to Skills section",
    ],
    "creator_tips": ["Post weekly about your AI projects", "Comment on recruiters' posts"],
    "profile_completeness_tips": ["Add a professional photo", "Set a custom LinkedIn URL"],
}

PROJECT_AGENT_RESPONSE = {
    "portfolio_score": 30,
    "portfolio_assessment": "Current portfolio lacks AI/ML projects. 3 targeted projects will significantly improve visibility.",
    "recommended_projects": [
        {
            "rank": 1,
            "title": "AI-Powered Resume Screener",
            "one_liner": "FastAPI + ChromaDB + Gemini API that scores resumes against job descriptions.",
            "description": "Build a FastAPI backend that accepts resume PDFs, embeds with Gemini, stores in ChromaDB, and scores against JD.",
            "why_this_impresses": "Directly demonstrates RAG, LLM integration, and async API design.",
            "skills_demonstrated": ["FastAPI", "ChromaDB", "Gemini API", "Docker"],
            "skills_learned": ["Vector embeddings", "Prompt engineering"],
            "estimated_weeks": 2,
            "difficulty": "intermediate",
            "tech_stack": {
                "backend": ["FastAPI", "Python"],
                "frontend": [],
                "ai_ml": ["Gemini API", "ChromaDB"],
                "database": ["PostgreSQL"],
                "devops": ["Docker"],
            },
            "github_readme_sections": ["Architecture", "Tech Stack", "Setup", "API Docs"],
            "interview_talking_points": [
                "How you chunked and embedded PDFs",
                "Why cosine similarity over keyword matching",
            ],
            "scale_question": "How would you handle 10,000 resumes/day?",
            "demo_tip": "Host a live demo on Render and paste any job description.",
        }
    ],
    "projects_to_avoid": [
        {"project": "Todo App", "reason": "Every tutorial builds this. Zero differentiation."},
        {"project": "Weather App", "reason": "Generic API consumption, no problem-solving signal."},
    ],
    "portfolio_target_score": 75,
    "portfolio_action_plan": ["Start with Project 1 this week", "Deploy each project publicly on Render"],
}

ENGLISH_AGENT_RESPONSE = {
    "original_text": "So basically I am uh a developer",
    "corrected_text": "I'm a Python developer with 2 years of experience building production APIs.",
    "scores": {"grammar": 72, "fluency": 65, "structure": 58, "vocabulary": 70, "conciseness": 60, "overall": 65},
    "issues": [
        {"type": "filler_word",  "found": "basically", "suggestion": "Remove entirely", "explanation": "Filler weakens the statement."},
        {"type": "filler_word",  "found": "uh",         "suggestion": "Replace with a silent pause", "explanation": "Uh signals uncertainty."},
        {"type": "grammar",      "found": "I am developer", "suggestion": "I'm a developer", "explanation": "Missing article."},
    ],
    "annotations": [
        {"original": "basically", "corrected": "[removed]", "reason": "Filler word"},
        {"original": "uh",        "corrected": "[pause]",   "reason": "Filler sound"},
    ],
    "star_compliance": {
        "situation": False, "task": False, "action": False, "result": False,
        "score": 0, "missing": "All four STAR components",
        "tip": "Start with the Situation — one sentence describing the context.",
    },
    "vocabulary_upgrades": [
        {"weak": "worked on", "strong": "engineered / architected", "context": "When describing technical work"},
    ],
    "practice_scripts": {
        "elevator_pitch_30s": "I build AI systems that ship to production. 2 years in backend and AI, most recently building a RAG pipeline.",
        "self_intro_2min": "I'm a Python developer specializing in AI systems...",
        "hr_answers": {"tell_me_about_yourself": "I'm a backend engineer with 2 years..."},
    },
    "top_3_improvements": [
        "Eliminate filler words (basically, uh)",
        "Add measurable result to every achievement",
        "Use strong action verbs (engineered, architected)",
    ],
    "encouragement": "Your technical vocabulary is solid. Eliminating filler words will immediately improve your score by 15+ points.",
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. UNIT TESTS — Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

class TestLinkedInPrompts:
    def test_build_linkedin_prompt_includes_role(self):
        from app.agents.personal.linkedin_prompts import build_linkedin_prompt
        prompt = build_linkedin_prompt(
            headline="Python Dev", about="I work with Python.", experience="Built APIs.",
            skills=["Python", "SQL"], target_role="AI Engineer", rag_context=[],
        )
        assert "AI Engineer" in prompt
        assert "Python Dev" in prompt

    def test_build_linkedin_prompt_includes_rag(self):
        from app.agents.personal.linkedin_prompts import build_linkedin_prompt
        prompt = build_linkedin_prompt(
            headline="", about="", experience="", skills=[],
            target_role="Data Scientist",
            rag_context=["LinkedIn scoring criteria: headline worth 20 points"],
        )
        assert "LinkedIn scoring criteria" in prompt

    def test_linkedin_system_prompt_has_json_instruction(self):
        from app.agents.personal.linkedin_prompts import LINKEDIN_SYSTEM
        assert "JSON" in LINKEDIN_SYSTEM
        assert "current_score" in LINKEDIN_SYSTEM
        assert "optimized_score" in LINKEDIN_SYSTEM

    def test_build_linkedin_prompt_handles_empty_skills(self):
        from app.agents.personal.linkedin_prompts import build_linkedin_prompt
        prompt = build_linkedin_prompt(
            headline="test", about="test", experience="test",
            skills=[], target_role="Backend Engineer", rag_context=[],
        )
        assert "Not provided" in prompt


class TestProjectPrompts:
    def test_build_project_prompt_includes_role_and_level(self):
        from app.agents.personal.project_recommendation_prompts import build_project_prompt
        prompt = build_project_prompt(
            target_role="ML Engineer", experience_level="1-2 years",
            time_available_weeks=4, current_skills=["Python", "TensorFlow"],
            missing_skills=["MLflow", "Docker"], existing_projects=["Churn model"],
            rag_context=[],
        )
        assert "ML Engineer" in prompt
        assert "1-2 years" in prompt
        assert "4 weeks" in prompt or "4-week" in prompt or "4" in prompt

    def test_build_project_prompt_excludes_existing_projects(self):
        from app.agents.personal.project_recommendation_prompts import build_project_prompt
        prompt = build_project_prompt(
            target_role="AI Engineer", experience_level="fresher",
            time_available_weeks=6, current_skills=[],
            missing_skills=[], existing_projects=["Weather App", "Todo App"],
            rag_context=[],
        )
        assert "Weather App" in prompt
        assert "Todo App" in prompt

    def test_project_system_prompt_requires_json(self):
        from app.agents.personal.project_recommendation_prompts import PROJECT_SYSTEM
        assert "JSON" in PROJECT_SYSTEM
        assert "recommended_projects" in PROJECT_SYSTEM


class TestEnglishPrompts:
    def test_build_english_eval_prompt_includes_context(self):
        from app.agents.personal.spoken_english_prompts import build_english_eval_prompt
        prompt = build_english_eval_prompt(
            spoken_text="So basically I am a developer",
            context_type="interview_answer",
            question_answered="Tell me about yourself",
            target_role="AI Engineer",
            resume_skills=["Python", "FastAPI"],
            rag_context=[],
        )
        assert "interview" in prompt.lower()
        assert "Tell me about yourself" in prompt
        assert "Python" in prompt

    def test_english_system_prompt_has_star_field(self):
        from app.agents.personal.spoken_english_prompts import ENGLISH_EVAL_SYSTEM
        assert "star_compliance" in ENGLISH_EVAL_SYSTEM
        assert "vocabulary_upgrades" in ENGLISH_EVAL_SYSTEM

    def test_build_script_prompt_includes_skills(self):
        from app.agents.personal.spoken_english_prompts import build_script_generation_prompt
        prompt = build_script_generation_prompt(
            target_role="Backend Engineer", skills=["Go", "gRPC"],
            experience_level="2-3 years", notable_projects=["Payment service"],
        )
        assert "Backend Engineer" in prompt
        assert "Go" in prompt
        assert "Payment service" in prompt


# ─────────────────────────────────────────────────────────────────────────────
# 2. UNIT TESTS — Response parsers / validators
# ─────────────────────────────────────────────────────────────────────────────

class TestLinkedInParser:
    def test_parse_valid_json(self):
        from app.agents.personal.linkedin_agent import _parse_linkedin_response
        raw = json.dumps(LINKEDIN_AGENT_RESPONSE)
        result = _parse_linkedin_response(raw)
        assert result["current_score"] == 35
        assert result["optimized_score"] == 78

    def test_parse_json_with_markdown_fence(self):
        from app.agents.personal.linkedin_agent import _parse_linkedin_response
        raw = f"```json\n{json.dumps(LINKEDIN_AGENT_RESPONSE)}\n```"
        result = _parse_linkedin_response(raw)
        assert result["current_score"] == 35

    def test_parse_invalid_json_returns_fallback(self):
        from app.agents.personal.linkedin_agent import _parse_linkedin_response
        result = _parse_linkedin_response("This is not JSON at all!")
        assert "error_reason" in result
        assert result["current_score"] == 0

    def test_validate_sets_defaults(self):
        from app.agents.personal.linkedin_agent import _validate_linkedin_output
        result = _validate_linkedin_output({})
        assert "current_score" in result
        assert "sections" in result
        assert "keyword_density" in result


class TestProjectParser:
    def test_parse_valid_json(self):
        from app.agents.personal.project_recommendation_agent import _parse_project_response
        raw = json.dumps(PROJECT_AGENT_RESPONSE)
        result = _parse_project_response(raw)
        assert result["portfolio_score"] == 30
        assert len(result["recommended_projects"]) == 1

    def test_parse_json_with_preamble_text(self):
        from app.agents.personal.project_recommendation_agent import _parse_project_response
        raw = f"Here are the recommendations:\n{json.dumps(PROJECT_AGENT_RESPONSE)}"
        result = _parse_project_response(raw)
        assert result["portfolio_score"] == 30

    def test_validate_sets_project_defaults(self):
        from app.agents.personal.project_recommendation_agent import _validate_project_output
        data = {"recommended_projects": [{"title": "Test Project"}]}
        result = _validate_project_output(data)
        p = result["recommended_projects"][0]
        assert p["rank"] == 1
        assert p["difficulty"] == "intermediate"
        assert isinstance(p["tech_stack"], dict)


class TestEnglishParser:
    def test_parse_valid_json(self):
        from app.agents.personal.spoken_english_agent import _parse_english_response
        raw = json.dumps(ENGLISH_AGENT_RESPONSE)
        result = _parse_english_response(raw)
        assert result["scores"]["overall"] == 65
        assert len(result["issues"]) == 3

    def test_parse_invalid_returns_fallback(self):
        from app.agents.personal.spoken_english_agent import _parse_english_response
        result = _parse_english_response("not valid json")
        assert "error_reason" in result
        assert result["scores"]["overall"] == 0

    def test_validate_sets_all_score_defaults(self):
        from app.agents.personal.spoken_english_agent import _validate_english_output
        result = _validate_english_output({})
        scores = result["scores"]
        for field in ("grammar", "fluency", "structure", "vocabulary", "conciseness", "overall"):
            assert field in scores


# ─────────────────────────────────────────────────────────────────────────────
# 3. AGENT NODE TESTS — with mocked LLM and RAG
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestLinkedInAgentNode:
    async def test_node_returns_linkedin_output(self):
        from app.agents.personal.linkedin_agent import linkedin_agent_node

        mock_response = MagicMock()
        mock_response.content = json.dumps(LINKEDIN_AGENT_RESPONSE)

        with patch("app.agents.personal.linkedin_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.linkedin_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm

                state = make_state()
                result = await linkedin_agent_node(state)

        assert "linkedin_output" in result
        assert result["linkedin_output"]["current_score"] == 35
        assert result["linkedin_output"]["optimized_score"] == 78
        assert "linkedin_agent" in result["agents_called"]

    async def test_node_fallback_when_no_content(self):
        from app.agents.personal.linkedin_agent import linkedin_agent_node

        state = make_state(
            linkedin_headline="",
            linkedin_about="",
            linkedin_experience="",
            linkedin_skills=[],
        )
        # No resume skills either
        state["resume_analysis"] = {}

        result = await linkedin_agent_node(state)

        assert "linkedin_output" in result
        assert "error_reason" in result["linkedin_output"]
        assert "linkedin_agent" in result["agents_called"]

    async def test_node_handles_llm_exception(self):
        from app.agents.personal.linkedin_agent import linkedin_agent_node

        with patch("app.agents.personal.linkedin_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.linkedin_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("Gemini rate limit"))
                mock_llm_fn.return_value = mock_llm

                state = make_state()
                result = await linkedin_agent_node(state)

        assert "error" in result
        assert "Gemini rate limit" in result["error"]
        assert result["error_agent"] == "linkedin_agent"

    async def test_node_uses_resume_skills_when_linkedin_skills_empty(self):
        """Agent should fall back to resume analysis skills if LinkedIn skills not provided."""
        from app.agents.personal.linkedin_agent import linkedin_agent_node

        mock_response = MagicMock()
        mock_response.content = json.dumps(LINKEDIN_AGENT_RESPONSE)

        with patch("app.agents.personal.linkedin_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.linkedin_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm

                # No LinkedIn skills, but resume has skills
                state = make_state(linkedin_skills=[])
                state["resume_analysis"] = {"extracted_skills": ["Python", "FastAPI"]}
                result = await linkedin_agent_node(state)

        # Should complete successfully (used resume skills)
        assert result["linkedin_output"]["current_score"] == 35


@pytest.mark.asyncio
class TestProjectAgentNode:
    async def test_node_returns_recommendations(self):
        from app.agents.personal.project_recommendation_agent import project_recommendation_agent_node

        mock_response = MagicMock()
        mock_response.content = json.dumps(PROJECT_AGENT_RESPONSE)

        with patch("app.agents.personal.project_recommendation_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.project_recommendation_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm

                state = make_state()
                result = await project_recommendation_agent_node(state)

        assert "project_recommendations_output" in result
        recs = result["project_recommendations_output"]
        assert recs["portfolio_score"] == 30
        assert len(recs["recommended_projects"]) == 1
        assert recs["recommended_projects"][0]["title"] == "AI-Powered Resume Screener"
        assert "project_recommendation_agent" in result["agents_called"]

    async def test_node_handles_llm_failure(self):
        from app.agents.personal.project_recommendation_agent import project_recommendation_agent_node

        with patch("app.agents.personal.project_recommendation_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.project_recommendation_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("API timeout"))
                mock_llm_fn.return_value = mock_llm

                state = make_state()
                result = await project_recommendation_agent_node(state)

        assert result["project_recommendations_output"]["recommended_projects"] == []
        assert "error" in result

    async def test_node_reads_skill_gap_state(self):
        """Agent should use skill_gap_analysis.priority_order as missing_skills."""
        from app.agents.personal.project_recommendation_agent import project_recommendation_agent_node

        mock_response = MagicMock()
        mock_response.content = json.dumps(PROJECT_AGENT_RESPONSE)

        with patch("app.agents.personal.project_recommendation_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.project_recommendation_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm

                # Provide skill gap data
                state = make_state()
                state["skill_gap_analysis"] = {"priority_order": ["MLflow", "Kubernetes", "Airflow"]}
                result = await project_recommendation_agent_node(state)

        # Should succeed and include the skill gap in the prompt (tested via mock called)
        assert "project_recommendations_output" in result
        mock_llm.ainvoke.assert_called_once()
        call_args = mock_llm.ainvoke.call_args[0][0]
        prompt_text = " ".join(m.content for m in call_args if hasattr(m, "content"))
        assert "MLflow" in prompt_text


@pytest.mark.asyncio
class TestEnglishAgentNode:
    async def test_node_evaluates_text(self):
        from app.agents.personal.spoken_english_agent import spoken_english_agent_node

        mock_response = MagicMock()
        mock_response.content = json.dumps(ENGLISH_AGENT_RESPONSE)

        with patch("app.agents.personal.spoken_english_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.spoken_english_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_llm_fn.return_value = mock_llm

                state = make_state(spoken_text="So basically I am uh a developer and I have been working on stuff")
                result = await spoken_english_agent_node(state)

        assert "english_output" in result
        out = result["english_output"]
        assert out["scores"]["overall"] == 65
        assert len(out["issues"]) == 3
        assert "spoken_english_agent" in result["agents_called"]

    async def test_node_switches_to_script_mode_for_empty_text(self):
        """If spoken_text is empty/short, agent generates scripts instead of evaluating."""
        from app.agents.personal.spoken_english_agent import spoken_english_agent_node

        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "elevator_pitch_30s": "I'm a Python dev.",
            "self_intro_2min": "I'm a Python developer...",
            "hr_answers": {},
        })

        with patch("app.agents.personal.spoken_english_agent.get_gemini_flash") as mock_llm_fn:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_fn.return_value = mock_llm

            state = make_state(spoken_text="")  # empty → script mode
            result = await spoken_english_agent_node(state)

        assert "english_output" in result
        scripts = result["english_output"].get("practice_scripts", {})
        assert "elevator_pitch_30s" in scripts

    async def test_node_handles_llm_exception(self):
        from app.agents.personal.spoken_english_agent import spoken_english_agent_node

        with patch("app.agents.personal.spoken_english_agent.enrich_state_with_rag",
                   new=AsyncMock(return_value={"rag_context": []})):
            with patch("app.agents.personal.spoken_english_agent.get_gemini_flash") as mock_llm_fn:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("Connection error"))
                mock_llm_fn.return_value = mock_llm

                state = make_state(spoken_text="So basically I am a developer who works on AI stuff")
                result = await spoken_english_agent_node(state)

        assert result["english_output"]["scores"]["overall"] == 0
        assert "error" in result


# ─────────────────────────────────────────────────────────────────────────────
# 4. API ROUTE TESTS — with mocked services
# ─────────────────────────────────────────────────────────────────────────────

def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    user.target_role = "AI Engineer"
    user.is_active = True
    return user


def make_linkedin_service_response():
    return {
        "optimization_id": str(uuid.uuid4()),
        "target_role": "AI Engineer",
        "result": LINKEDIN_AGENT_RESPONSE,
        "agent_error": None,
        "optimized_at": datetime.now(timezone.utc).isoformat(),
    }


def make_project_service_response():
    return {
        "recommendation_id": str(uuid.uuid4()),
        "target_role": "AI Engineer",
        "experience_level": "1-2 years",
        "result": PROJECT_AGENT_RESPONSE,
        "agent_error": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def make_english_service_response():
    return {
        "evaluation_id": str(uuid.uuid4()),
        "context_type": "interview_answer",
        "result": ENGLISH_AGENT_RESPONSE,
        "agent_error": None,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.mark.asyncio
class TestLinkedInRoutes:
    async def test_optimize_returns_200(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        with patch("app.api.routes.linkedin.run_linkedin_optimization",
                   new=AsyncMock(return_value=make_linkedin_service_response())):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/api/linkedin/optimize", json={
                    "target_role": "AI Engineer",
                    "headline": "Python Dev",
                    "about": "I work with Python.",
                    "experience": "Built APIs.",
                    "skills": ["Python"],
                })

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "optimization_id" in data
        assert data["result"]["current_score"] == 35
        assert data["result"]["optimized_score"] == 78

        app.dependency_overrides.clear()

    async def test_optimize_requires_target_role(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post("/api/linkedin/optimize", json={
                "headline": "Python Dev",
                # missing target_role
            })

        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()

    async def test_history_returns_list(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        mock_history = [
            {"optimization_id": str(uuid.uuid4()), "target_role": "AI Engineer",
             "current_score": 35, "optimized_score": 78,
             "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        with patch("app.api.routes.linkedin.get_linkedin_history",
                   new=AsyncMock(return_value=mock_history)):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.get("/api/linkedin/history")

        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.json(), list)
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestProjectRoutes:
    async def test_recommend_returns_200(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        with patch("app.api.routes.projects.run_project_recommendations",
                   new=AsyncMock(return_value=make_project_service_response())):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/api/projects/recommend", json={
                    "target_role": "AI Engineer",
                    "experience_level": "1-2 years",
                    "time_available_weeks": 4,
                })

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "recommendation_id" in data
        assert data["result"]["portfolio_score"] == 30
        assert len(data["result"]["recommended_projects"]) == 1
        assert data["result"]["recommended_projects"][0]["title"] == "AI-Powered Resume Screener"

        app.dependency_overrides.clear()

    async def test_recommend_validates_experience_level(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post("/api/projects/recommend", json={
                "target_role": "AI Engineer",
                "experience_level": "not_a_valid_level",  # invalid enum
            })

        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()

    async def test_recommend_defaults_time_weeks(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        with patch("app.api.routes.projects.run_project_recommendations",
                   new=AsyncMock(return_value=make_project_service_response())) as mock_svc:
            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.post("/api/projects/recommend", json={
                    "target_role": "Backend Engineer",
                    # no time_available_weeks → should default to 4
                })

        call_kwargs = mock_svc.call_args.kwargs
        assert call_kwargs["time_available_weeks"] == 4
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestEnglishRoutes:
    async def test_evaluate_returns_200(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        with patch("app.api.routes.english.run_english_evaluation",
                   new=AsyncMock(return_value=make_english_service_response())):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/api/english/evaluate", json={
                    "spoken_text": "So basically I am uh a developer and I have been working on Python and stuff for 2 years.",
                    "context_type": "interview_answer",
                    "question": "Tell me about yourself",
                })

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "evaluation_id" in data
        assert data["result"]["scores"]["overall"] == 65
        assert len(data["result"]["issues"]) == 3

        app.dependency_overrides.clear()

    async def test_evaluate_rejects_short_text(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post("/api/english/evaluate", json={
                "spoken_text": "hi",  # too short (< 20 chars)
                "context_type": "interview_answer",
            })

        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()

    async def test_generate_scripts_returns_200(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        mock_script_data = {
            "scripts": {
                "elevator_pitch_30s": "I'm a Python developer...",
                "self_intro_2min": "I'm a backend engineer with 2 years...",
                "hr_answers": {"tell_me_about_yourself": "I build backend APIs..."},
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("app.api.routes.english.run_script_generation",
                   new=AsyncMock(return_value=mock_script_data)):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/api/english/scripts", json={
                    "experience_level": "1-2 years",
                })

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "scripts" in data
        assert data["scripts"]["elevator_pitch_30s"]

        app.dependency_overrides.clear()

    async def test_english_history_returns_list(self):
        from app.main import app
        from app.api.dependencies import get_current_active_user
        from app.db.database import get_db

        app.dependency_overrides[get_current_active_user] = lambda: mock_user()
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        mock_history = [
            {"evaluation_id": str(uuid.uuid4()), "context_type": "interview_answer",
             "overall_score": 65, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        with patch("app.api.routes.english.get_english_history",
                   new=AsyncMock(return_value=mock_history)):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.get("/api/english/history")

        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.json(), list)
        assert resp.json()[0]["overall_score"] == 65
        app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# 5. STATE INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestPhase2StateFields:
    def test_create_initial_state_has_phase2_fields(self):
        from app.agents.state import create_initial_state
        state = create_initial_state(
            user_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            user_message="Optimize my LinkedIn",
            linkedin_headline="Test headline",
            linkedin_skills=["Python"],
        )
        assert "linkedin_headline" in state
        assert state["linkedin_headline"] == "Test headline"
        assert state["linkedin_output"] == {}
        assert state["project_recommendations_output"] == {}
        assert state["english_output"] == {}

    def test_agent_names_include_phase2(self):
        from app.agents.state import AgentName
        assert AgentName.LINKEDIN == "linkedin_agent"
        assert AgentName.PROJECT_RECOMMEND == "project_recommendation_agent"
        assert AgentName.SPOKEN_ENGLISH == "spoken_english_agent"
        assert AgentName.LINKEDIN in AgentName.ALL_AGENTS
        assert AgentName.PROJECT_RECOMMEND in AgentName.ALL_AGENTS
        assert AgentName.SPOKEN_ENGLISH in AgentName.ALL_AGENTS

    def test_phase2_agents_not_in_phase1_list(self):
        from app.agents.state import AgentName
        assert AgentName.LINKEDIN not in AgentName.PHASE_1_AGENTS
        assert AgentName.PROJECT_RECOMMEND not in AgentName.PHASE_1_AGENTS
        assert AgentName.SPOKEN_ENGLISH not in AgentName.PHASE_1_AGENTS

    def test_all_agents_is_union_of_phase1_and_phase2(self):
        from app.agents.state import AgentName
        expected = set(AgentName.PHASE_1_AGENTS) | set(AgentName.PHASE_2_AGENTS)
        assert set(AgentName.ALL_AGENTS) == expected


# ─────────────────────────────────────────────────────────────────────────────
# 6. RAG RETRIEVER TESTS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestPhase2Retrievers:
    async def test_retrieve_linkedin_templates_calls_correct_collection(self):
        from app.rag.retriever import retrieve_linkedin_templates

        with patch("app.rag.retriever._query_collection",
                   new=AsyncMock(return_value=["LinkedIn headline template: ..."])) as mock_q:
            results = await retrieve_linkedin_templates("AI engineer headline", section_type="headline")

        assert isinstance(results, list)
        mock_q.assert_called_once()
        call_args = mock_q.call_args
        assert call_args[0][0] == "linkedin_templates"  # correct collection

    async def test_retrieve_project_templates_with_filters(self):
        from app.rag.retriever import retrieve_project_templates

        with patch("app.rag.retriever._query_collection",
                   new=AsyncMock(return_value=["Project: RAG chatbot..."])) as mock_q:
            results = await retrieve_project_templates(
                "AI project ideas", role_category="ai_ml", difficulty="intermediate"
            )

        assert isinstance(results, list)
        mock_q.assert_called_once()
        call_kwargs = mock_q.call_args
        # where filter should have been passed
        assert call_kwargs[0][0] == "project_templates"

    async def test_retrieve_english_templates_with_context_filter(self):
        from app.rag.retriever import retrieve_english_templates

        with patch("app.rag.retriever._query_collection",
                   new=AsyncMock(return_value=["STAR format example..."])) as mock_q:
            results = await retrieve_english_templates(
                "STAR format interview answer", template_type="hr_answer", context="interview"
            )

        assert isinstance(results, list)
        mock_q.assert_called_once()
        assert mock_q.call_args[0][0] == "english_templates"
