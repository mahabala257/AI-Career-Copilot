"""
app/rag/rag_pipeline.py
────────────────────────
The unified RAG pipeline — the single entry point agents use to get context.

Why this layer on top of retriever.py?
────────────────────────────────────────
retriever.py knows HOW to query ChromaDB.
rag_pipeline.py knows WHAT to query for each agent and WHEN.

This layer:
  1. Decides what query string to build per agent
  2. Decides which filters to apply
  3. Calls retriever, gets chunks
  4. Injects chunks into the LangGraph state["rag_context"] field
  5. Provides a single async function agents call before their LLM call

Usage pattern (in every real agent node):
─────────────────────────────────────────
  # At the top of each agent node function:
  enriched_state = await enrich_state_with_rag(state, AgentName.RESUME)
  rag_context = enriched_state.get("rag_context", [])

  # Then inject rag_context into the Gemini prompt:
  human_prompt = build_resume_analysis_prompt(
      resume_text=resume_text,
      target_role=target_role,
      rag_context=rag_context,   # <-- RAG chunks go here
  )

Graceful degradation
──────────────────────
If ChromaDB is empty (not yet seeded), RAG returns empty list.
Agents still work — they just rely on Gemini's training data alone.
This is the correct behaviour: RAG improves quality, but absence doesn't break anything.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.state import AgentName, CareerCopilotState
from app.rag.retriever import (
    retrieve_career_guidance,
    retrieve_for_agent,
    retrieve_interview_questions,
    retrieve_job_requirements,
    retrieve_learning_resources,
    retrieve_linkedin_templates,
    retrieve_project_templates,
    retrieve_english_templates,
    retrieve_company_information,
    retrieve_internship_information,
    retrieve_wellness_resources,
)


logger = logging.getLogger(__name__)


async def enrich_state_with_rag(
    state: CareerCopilotState,
    agent_name: str,
) -> dict[str, Any]:
    """
    Main entry point called by each agent before its LLM call.

    Builds the right query from state, calls the retriever,
    returns a dict with rag_context set.

    Returns partial state update dict (only rag_context key).
    """
    target_role = state.get("target_role", "")
    user_message = state.get("user_message", "")

    try:
        chunks = await _build_rag_context(
            agent_name=agent_name,
            state=state,
            target_role=target_role,
            user_message=user_message,
        )
        logger.info(f"[RAG] {agent_name}: retrieved {len(chunks)} chunks for role='{target_role}'")
        return {"rag_context": chunks}

    except Exception as e:
        logger.error(f"[RAG] Pipeline error for {agent_name}: {e}")
        return {"rag_context": []}


async def _build_rag_context(
    agent_name: str,
    state: CareerCopilotState,
    target_role: str,
    user_message: str,
) -> list[str]:
    """
    Build RAG context specific to each agent's needs.
    Each agent gets the most relevant context for its task.
    """

    # ── Resume Agent ─────────────────────────────────────────────────────────
    if agent_name == AgentName.RESUME:
        # Resume agent needs: what skills are required for this role
        if target_role:
            return await retrieve_job_requirements(target_role, n_results=6)
        return await retrieve_for_agent(AgentName.RESUME, user_message, n_results=5)

    # ── Skill Gap Agent ───────────────────────────────────────────────────────
    elif agent_name == AgentName.SKILL_GAP:
        # Skill gap needs: job requirements + career progression advice
        chunks = []
        if target_role:
            job_chunks = await retrieve_job_requirements(target_role, n_results=5)
            chunks.extend(job_chunks)

        guidance_query = f"career path progression skills for {target_role}"
        guidance_chunks = await retrieve_career_guidance(guidance_query, n_results=3)
        chunks.extend(guidance_chunks)
        return chunks

    # ── Interview Agent ───────────────────────────────────────────────────────
    elif agent_name == AgentName.INTERVIEW:
        interview_type = state.get("interview_type", "technical")
        difficulty     = state.get("quiz_difficulty", "medium")
        if target_role:
            return await retrieve_interview_questions(
                role=target_role,
                interview_type=interview_type,
                difficulty=difficulty,
                n_results=8,
            )
        return await retrieve_for_agent(AgentName.INTERVIEW, user_message, n_results=6)

    # ── Quiz Agent ────────────────────────────────────────────────────────────
    elif agent_name == AgentName.QUIZ:
        topic = state.get("quiz_topic", "")
        if not topic and target_role:
            # Derive topic from role if not specified
            topic = target_role
        query = f"{topic} study materials tutorials learning resources" if topic else user_message
        return await retrieve_learning_resources(topic or user_message, n_results=5)

    # ── Study Planner Agent ───────────────────────────────────────────────────
    elif agent_name == AgentName.STUDY_PLANNER:
        chunks = []

        # Get learning resources for the priority skills
        skill_gap = state.get("skill_gap_analysis", {})
        priority  = skill_gap.get("priority_order", [])[:3]

        for skill in priority:
            skill_chunks = await retrieve_learning_resources(skill, n_results=2)
            chunks.extend(skill_chunks)

        # Get career planning guidance
        plan_query = f"study plan learning schedule for {target_role}"
        guidance   = await retrieve_career_guidance(plan_query, n_results=3)
        chunks.extend(guidance)

        return chunks[:8]  # cap total

    # ── LinkedIn Optimization Agent ───────────────────────────────────────────
    elif agent_name == AgentName.LINKEDIN:
        chunks = []

        # Scoring rubric first — always include
        scoring = await retrieve_linkedin_templates(
            "LinkedIn profile scoring criteria sections",
            section_type="scoring",
            n_results=1,
        )
        chunks.extend(scoring)

        # Role-specific keywords
        if target_role:
            role_category = _infer_role_category(target_role)
            keywords = await retrieve_linkedin_templates(
                f"LinkedIn keywords for {target_role}",
                section_type="keywords",
                role_category=role_category,
                n_results=2,
            )
            chunks.extend(keywords)

            # Headline and About templates for the role
            templates = await retrieve_linkedin_templates(
                f"{target_role} LinkedIn headline about section example",
                role_category=role_category,
                n_results=3,
            )
            chunks.extend(templates)

        # Experience bullet patterns — always useful
        bullets = await retrieve_linkedin_templates(
            "STAR format experience bullet points strong action verbs",
            section_type="experience",
            n_results=2,
        )
        chunks.extend(bullets)

        return chunks[:8]

    # ── Project Recommendation Agent ──────────────────────────────────────────
    elif agent_name == AgentName.PROJECT_RECOMMEND:
        chunks = []

        experience_level = state.get("experience_level", "fresher")
        difficulty = _experience_to_difficulty(experience_level)
        role_category = _infer_role_category(target_role) if target_role else "general"

        # Role-matched project templates
        project_chunks = await retrieve_project_templates(
            f"project ideas for {target_role} {experience_level}",
            role_category=role_category,
            difficulty=difficulty,
            n_results=6,
        )
        chunks.extend(project_chunks)

        # Always add the "avoid" list
        avoid_chunks = await retrieve_project_templates(
            "projects to avoid overused portfolio anti-patterns",
            n_results=1,
        )
        chunks.extend(avoid_chunks)

        return chunks[:8]

    # ── Spoken English Agent ──────────────────────────────────────────────────
    elif agent_name == AgentName.SPOKEN_ENGLISH:
        chunks = []
        context_type = state.get("english_context_type", "interview_answer")
        spoken_text  = state.get("spoken_text", "")

        # Filler words guide — always include
        fillers = await retrieve_english_templates(
            "filler words uh um basically professional speech",
            template_type="filler_words",
            n_results=1,
        )
        chunks.extend(fillers)

        # Vocabulary upgrades
        vocab = await retrieve_english_templates(
            "professional vocabulary upgrades weak strong words interview",
            template_type="vocab_upgrade",
            n_results=2,
        )
        chunks.extend(vocab)

        # Context-specific: interview → STAR + model answers
        if context_type in ("interview_answer", "self_intro"):
            star = await retrieve_english_templates(
                f"STAR format {user_message or 'interview answer example'}",
                template_type="hr_answer",
                context="interview",
                n_results=3,
            )
            chunks.extend(star)

        # Grammar patterns
        grammar = await retrieve_english_templates(
            "grammar mistakes corrections Indian English professional",
            template_type="grammar",
            n_results=1,
        )
        chunks.extend(grammar)

        return chunks[:8]

    # ── Company Research Agent ────────────────────────────────────────────────
    elif agent_name == AgentName.COMPANY_RESEARCH:
        chunks = []
        company_name = state.get("company_name", "")

        if company_name:
            company_chunks = await retrieve_company_information(
                f"{company_name} interview process tech stack culture",
                company=company_name,
                n_results=6,
            )
            chunks.extend(company_chunks)

            # If no company-specific docs found, fall back to general query
            if not company_chunks:
                general_chunks = await retrieve_company_information(
                    f"{company_name} {target_role} interview preparation",
                    n_results=4,
                )
                chunks.extend(general_chunks)

        return chunks[:8]

    # ── Internship Research Agent ─────────────────────────────────────────────
    elif agent_name == AgentName.INTERNSHIP_RESEARCH:
        chunks = []
        education_level = state.get("education_level", "")

        program_chunks = await retrieve_internship_information(
            f"internship programs for {target_role} {education_level}",
            education_level="undergraduate" if education_level else None,
            n_results=5,
        )
        chunks.extend(program_chunks)

        timeline_chunks = await retrieve_internship_information(
            "internship application timeline when to apply",
            n_results=2,
        )
        chunks.extend(timeline_chunks)

        skills_chunks = await retrieve_internship_information(
            "skills required for internships preparation",
            n_results=2,
        )
        chunks.extend(skills_chunks)

        return chunks[:8]

    # ── Wellness & Motivation Agent ───────────────────────────────────────────
    elif agent_name == AgentName.WELLNESS:
        chunks = []
        mood_message = state.get("mood_message", "")

        situation = _infer_wellness_situation(mood_message)
        situation_chunks = await retrieve_wellness_resources(
            mood_message or "job search motivation support",
            situation=situation,
            n_results=3,
        )
        chunks.extend(situation_chunks)

        # Always include a motivational quote
        quote_chunks = await retrieve_wellness_resources(
            "motivational quote encouragement",
            situation="general",
            n_results=1,
        )
        chunks.extend(quote_chunks)

        return chunks[:6]

    # ── Default fallback ──────────────────────────────────────────────────────
    else:
        return await retrieve_for_agent(agent_name, user_message or target_role, n_results=4)


async def get_rag_health() -> dict:
    """
    Check RAG layer health: are collections seeded?
    Used by /health endpoint.
    """
    try:
        from app.rag.ingestion.loader import get_ingestion_status
        status = get_ingestion_status()
        all_seeded = all(v["seeded"] for v in status.values())
        total_docs = sum(v["count"] for v in status.values())
        return {
            "status":     "ready" if all_seeded else "needs_seeding",
            "total_docs": total_docs,
            "collections": status,
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "total_docs": 0}


def _infer_role_category(target_role: str) -> str:
    """Map a free-text role to a ChromaDB metadata category for filtered retrieval."""
    role_lower = target_role.lower()
    if any(k in role_lower for k in ["ai", "ml", "machine learning", "nlp", "llm", "data sci"]):
        return "ai_ml"
    if any(k in role_lower for k in ["data analyst", "data engineer", "analytics", "bi "]):
        return "data"
    if any(k in role_lower for k in ["full stack", "fullstack", "frontend", "react", "vue"]):
        return "fullstack"
    if any(k in role_lower for k in ["backend", "sde", "swe", "software eng", "java", "python dev"]):
        return "backend"
    return "general"


def _experience_to_difficulty(experience_level: str) -> str:
    """Map experience level to project difficulty for filtered retrieval."""
    mapping = {
        "fresher": "beginner",
        "0-1 years": "beginner",
        "1-2 years": "intermediate",
        "2-3 years": "intermediate",
        "3-5 years": "advanced",
        "5+ years": "advanced",
    }
    return mapping.get(experience_level, "intermediate")


def _infer_wellness_situation(mood_message: str) -> Optional[str]:
    """Map a free-text mood message to a wellness metadata situation tag."""
    if not mood_message:
        return None
    lower = mood_message.lower()
    if any(k in lower for k in ["reject", "didn't get", "turned down", "didn't make it"]):
        return "rejection"
    if any(k in lower for k in ["burnt out", "burnout", "exhausted", "tired of", "can't anymore"]):
        return "burnout"
    if any(k in lower for k in ["not good enough", "imposter", "don't deserve", "fake"]):
        return "imposter_syndrome"
    if any(k in lower for k in ["everyone else", "compared to", "behind", "others got"]):
        return "comparison"
    return None
