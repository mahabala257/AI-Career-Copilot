"""
app/rag/retriever.py
─────────────────────
The retrieval layer — queries ChromaDB and returns relevant document chunks.

How retrieval integrates with agents
──────────────────────────────────────
Each agent calls retrieve_for_agent() BEFORE its Gemini call.
The retrieved chunks are injected into the prompt as context:

  # In resume_agent_node:
  rag_context = await retrieve_for_agent(
      agent_name=AgentName.RESUME,
      query=f"skills required for {target_role}",
      filters={"role": target_role},
  )
  state["rag_context"] = rag_context
  # Then rag_context is injected into the Gemini prompt

This grounds Gemini's analysis in actual job market data rather than
relying solely on its training data (which may be outdated).

Query strategy per agent
─────────────────────────
  Resume Agent      → job_requirements collection, filtered by target_role
  Skill Gap Agent   → job_requirements + career_guidance collections
  Interview Agent   → interview_questions collection, filtered by role+type
  Quiz Agent        → learning_resources collection, filtered by topic
  Study Planner     → learning_resources + career_guidance collections

Result formatting
──────────────────
retrieve_for_agent() returns list[str] — plain text chunks ready to be
joined with newlines and dropped directly into a prompt template.

Each chunk includes its source metadata in brackets so Gemini can
attribute information: "[Source: interview_questions | role:AI Engineer]"
"""

import asyncio
import logging
from typing import Optional

from app.agents.state import AgentName
from app.rag.chromadb_client import (
    CollectionName,
    get_collection,
    get_embedding_function,
)

logger = logging.getLogger(__name__)

# Number of documents to retrieve per query
DEFAULT_N_RESULTS = 5
MAX_N_RESULTS     = 10


async def retrieve_for_agent(
    agent_name: str,
    query: str,
    n_results: int = DEFAULT_N_RESULTS,
    filters: Optional[dict] = None,
) -> list[str]:
    """
    Main retrieval entry point for all agents.

    Selects the appropriate collection(s) for the agent,
    performs semantic search, and returns formatted text chunks.

    Args:
        agent_name: One of AgentName constants (determines which collection)
        query:      Natural language query (e.g. "skills needed for AI Engineer")
        n_results:  How many chunks to retrieve
        filters:    ChromaDB where clause dict (e.g. {"role": "AI Engineer"})

    Returns:
        List of text strings, each a relevant document chunk with source label.
        Returns [] if collection is empty or query fails gracefully.
    """
    collection_name = _agent_to_collection(agent_name)

    if not collection_name:
        logger.debug(f"[RAG] No collection mapped for agent: {agent_name}")
        return []

    # Some agents benefit from querying multiple collections
    if isinstance(collection_name, list):
        results = []
        per_col = max(2, n_results // len(collection_name))
        for col_name in collection_name:
            chunks = await _query_collection(col_name, query, per_col, filters)
            results.extend(chunks)
        return results[:n_results]

    return await _query_collection(collection_name, query, n_results, filters)


async def retrieve_interview_questions(
    role: str,
    interview_type: str,
    difficulty: str = "medium",
    n_results: int = 8,
) -> list[str]:
    """
    Specialised retrieval for the Interview Agent.
    Builds a targeted query combining role, type, and difficulty.
    """
    query = f"{interview_type} interview questions for {role} {difficulty} level"
    filters = {"interview_type": interview_type}

    return await _query_collection(
        CollectionName.INTERVIEW_QUESTIONS,
        query,
        n_results,
        filters,
    )


async def retrieve_job_requirements(
    role: str,
    n_results: int = 6,
) -> list[str]:
    """
    Retrieve skill requirements for a specific role.
    Used by Resume Agent and Skill Gap Agent.
    """
    query = f"required skills and technologies for {role} position job description"
    return await _query_collection(
        CollectionName.JOB_REQUIREMENTS,
        query,
        n_results,
        where={"$or": [{"role": role}, {"category": "general"}]},
    )


async def retrieve_learning_resources(
    topic: str,
    n_results: int = 5,
) -> list[str]:
    """
    Retrieve learning resources for a specific topic.
    Used by Quiz Agent and Study Planner Agent.
    """
    query = f"how to learn {topic} courses tutorials resources"
    return await _query_collection(
        CollectionName.LEARNING_RESOURCES,
        query,
        n_results,
    )


async def retrieve_career_guidance(
    query: str,
    n_results: int = 4,
) -> list[str]:
    """
    Retrieve career advice and guidance.
    Used by Study Planner and Career Strategy Agent (Phase 2).
    """
    return await _query_collection(
        CollectionName.CAREER_GUIDANCE,
        query,
        n_results,
    )


# ── Phase 2 Retrieval Functions ────────────────────────────────────────────────

async def retrieve_linkedin_templates(
    query: str,
    section_type: Optional[str] = None,
    role_category: Optional[str] = None,
    n_results: int = 6,
) -> list[str]:
    """
    Retrieve LinkedIn profile templates and keyword lists.
    Used by LinkedIn Optimization Agent.

    Args:
        query:         Semantic query (e.g. "AI engineer headline template")
        section_type:  Optional filter — "headline" | "about" | "experience" | "keywords" | "scoring"
        role_category: Optional filter — "ai_ml" | "backend" | "data" | "general"
        n_results:     Max chunks to return
    """
    where = None
    if section_type:
        where = {"section_type": section_type}

    return await _query_collection(
        CollectionName.LINKEDIN_TEMPLATES,
        query,
        n_results,
        where=where,
    )


async def retrieve_project_templates(
    query: str,
    role_category: Optional[str] = None,
    difficulty: Optional[str] = None,
    n_results: int = 8,
) -> list[str]:
    """
    Retrieve project ideas matching a role and difficulty level.
    Used by Project Recommendation Agent.

    Args:
        query:         Semantic query (e.g. "AI project ideas for backend engineer")
        role_category: Optional filter — "ai_ml" | "backend" | "data" | "fullstack"
        difficulty:    Optional filter — "beginner" | "intermediate" | "advanced"
        n_results:     Max chunks to return
    """
    where = None
    if role_category and difficulty:
        where = {"role_category": role_category, "difficulty": difficulty}
    elif role_category:
        where = {"role_category": role_category}
    elif difficulty:
        where = {"difficulty": difficulty}

    return await _query_collection(
        CollectionName.PROJECT_TEMPLATES,
        query,
        n_results,
        where=where,
    )


async def retrieve_english_templates(
    query: str,
    template_type: Optional[str] = None,
    context: Optional[str] = None,
    n_results: int = 6,
) -> list[str]:
    """
    Retrieve English improvement templates and model answers.
    Used by Spoken English Agent.

    Args:
        query:         Semantic query (e.g. "tell me about yourself answer")
        template_type: Optional filter — "hr_answer" | "filler_words" | "vocab_upgrade" | "grammar"
        context:       Optional filter — "interview" | "email" | "presentation"
        n_results:     Max chunks to return
    """
    where = None
    if template_type and context:
        where = {"template_type": template_type, "context": context}
    elif template_type:
        where = {"template_type": template_type}
    elif context:
        where = {"context": context}

    return await _query_collection(
        CollectionName.ENGLISH_TEMPLATES,
        query,
        n_results,
        where=where,
    )


# ── Core query function ────────────────────────────────────────────────────────

async def retrieve_company_information(
    query: str,
    company: Optional[str] = None,
    n_results: int = 6,
) -> list[str]:
    """
    Retrieve company tech stack, interview process, and culture info.
    Used by Company Research Agent.
    """
    where = {"company": company.lower()} if company else None
    return await _query_collection(
        CollectionName.COMPANY_INFORMATION,
        query,
        n_results,
        where=where,
    )


async def retrieve_internship_information(
    query: str,
    company: Optional[str] = None,
    education_level: Optional[str] = None,
    n_results: int = 6,
) -> list[str]:
    """
    Retrieve internship program details, timelines, and skill requirements.
    Used by Internship Research Agent.
    """
    where = None
    if company and education_level:
        where = {"company": company.lower(), "education_level": education_level}
    elif company:
        where = {"company": company.lower()}
    elif education_level:
        where = {"education_level": education_level}

    return await _query_collection(
        CollectionName.INTERNSHIP_INFORMATION,
        query,
        n_results,
        where=where,
    )


async def retrieve_wellness_resources(
    query: str,
    situation: Optional[str] = None,
    n_results: int = 4,
) -> list[str]:
    """
    Retrieve wellness reframes, burnout strategies, and motivational content.
    Used by Wellness & Motivation Agent.
    """
    where = {"situation": situation} if situation else None
    return await _query_collection(
        CollectionName.WELLNESS_RESOURCES,
        query,
        n_results,
        where=where,
    )


async def _query_collection(
    collection_name: str,
    query: str,
    n_results: int,
    where: Optional[dict] = None,
) -> list[str]:
    """
    Execute a semantic similarity search against a ChromaDB collection.

    Returns formatted text chunks. Returns empty list gracefully on any error —
    agents must work even without RAG (degrade gracefully, not crash).
    """
    if not query or not query.strip():
        return []

    try:
        col = get_collection(collection_name)
        if col is None:
            logger.debug(f"[RAG] Collection '{collection_name}' not found or empty")
            return []

        # BUG-06 FIX: col.count() is synchronous and would block the event loop.
        # Offload it to a thread-pool worker via run_in_executor.
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(None, col.count)
        if count == 0:
            logger.debug(f"[RAG] Collection '{collection_name}' has 0 documents")
            return []

        # Cap n_results to available documents
        actual_n = min(n_results, count, MAX_N_RESULTS)

        # Build query kwargs
        query_kwargs: dict = {
            "query_texts": [query],
            "n_results": actual_n,
            "include": ["documents", "metadatas", "distances"],
        }

        # Add metadata filter if provided. ChromaDB 1.x requires multi-condition
        # filters to use an explicit $and operator (a plain multi-key dict is
        # rejected with "Expected where to have exactly one operator").
        if where:
            if len(where) > 1 and not any(k.startswith("$") for k in where):
                where = {"$and": [{k: v} for k, v in where.items()]}
            query_kwargs["where"] = where

        # BUG-06 FIX: col.query() is also synchronous — offload to thread pool.
        results = await loop.run_in_executor(
            None, lambda: col.query(**query_kwargs)
        )

        # Format results as labelled text chunks
        chunks = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            if not doc:
                continue

            # Include source label so Gemini knows where the info comes from
            source_parts = []
            if meta.get("role"):
                source_parts.append(f"role:{meta['role']}")
            if meta.get("category"):
                source_parts.append(f"category:{meta['category']}")
            if meta.get("source"):
                source_parts.append(f"source:{meta['source']}")

            source_label = " | ".join(source_parts) if source_parts else collection_name
            relevance = round((1 - dist) * 100)  # cosine: 1-dist = similarity

            # Only include reasonably relevant results (>40% similarity)
            if relevance >= 40:
                chunks.append(f"[{source_label} | relevance:{relevance}%]\n{doc}")

        logger.debug(
            f"[RAG] '{collection_name}' query='{query[:50]}' "
            f"→ {len(chunks)}/{actual_n} relevant chunks"
        )
        return chunks

    except Exception as e:
        # Never crash an agent because of a RAG failure
        logger.error(f"[RAG] Query failed for '{collection_name}': {e}")
        return []


# ── Collection routing ─────────────────────────────────────────────────────────

def _agent_to_collection(agent_name: str) -> Optional[str | list[str]]:
    """Map agent names to their primary collection(s)."""
    mapping = {
        AgentName.RESUME:         CollectionName.JOB_REQUIREMENTS,
        AgentName.SKILL_GAP:      [CollectionName.JOB_REQUIREMENTS, CollectionName.CAREER_GUIDANCE],
        AgentName.INTERVIEW:      CollectionName.INTERVIEW_QUESTIONS,
        AgentName.QUIZ:           CollectionName.LEARNING_RESOURCES,
        AgentName.STUDY_PLANNER:  [CollectionName.LEARNING_RESOURCES, CollectionName.CAREER_GUIDANCE],
        # Phase 2
        "material_agent":         CollectionName.LEARNING_RESOURCES,
        "company_research_agent": CollectionName.COMPANY_INFO,
        "career_strategy_agent":  CollectionName.CAREER_GUIDANCE,
    }
    return mapping.get(agent_name)
