"""
app/agents/state.py
────────────────────
The CareerCopilotState TypedDict is the SINGLE source of truth that all
agents in the LangGraph graph read from and write to.

How LangGraph state works
─────────────────────────
LangGraph passes the state dict through every node (agent). Each node
receives the full current state and returns a partial dict — only the
keys it wants to update. LangGraph merges those updates back into the
state before calling the next node.

Example:
  State enters supervisor:  { user_message: "analyze my resume", next_agent: "" }
  Supervisor returns:        { next_agent: "resume_agent", routing_reasoning: "..." }
  State now has both:        { user_message: "...", next_agent: "resume_agent", ... }

Why one big shared state instead of per-agent state?
  - Agents can read each other's outputs without extra plumbing
    (e.g. Study Planner reads skill_gaps from Skill Gap Agent)
  - The supervisor always has the full picture to make routing decisions
  - LangFuse traces get the complete session context in one object
  - Checkpointing (MemorySaver) saves/restores the entire session cleanly

Field groups
────────────
  1. Identity      — who is the user, what session is this
  2. Input         — what the user sent this turn
  3. Agent control — supervisor routing decisions
  4. Resume        — Resume Agent outputs
  5. Skills        — Skill Gap Agent outputs
  6. Interview     — Interview Agent outputs
  7. Quiz          — Quiz Agent outputs
  8. Study Plan    — Study Planner Agent outputs
  9. RAG           — retrieved context injected into agents
  10. Output        — final synthesized response to user
  11. Error         — error capture without crashing the graph
"""

from typing import Annotated, Any
from typing_extensions import TypedDict
import operator


# ── Reducer helpers ────────────────────────────────────────────────────────────
# LangGraph uses "reducers" to decide HOW to merge a field when multiple
# nodes update it. The default is "last write wins".
#
# For list fields like agents_called and messages, we want to APPEND rather
# than replace, so we use operator.add as the reducer.
# Annotated[list[str], operator.add] means: when merging, concatenate lists.

def _merge_dict(existing: dict, new: dict) -> dict:
    """Merge dicts instead of replacing. Used for partial updates to nested dicts."""
    if existing is None:
        return new
    if new is None:
        return existing
    return {**existing, **new}


class CareerCopilotState(TypedDict, total=False):
    """
    Shared state for the AI Career Copilot LangGraph workflow.

    total=False means all fields are optional — nodes only need to return
    the fields they update. Missing fields default to None unless a reducer
    handles them differently.
    """

    # ── 1. Identity ────────────────────────────────────────────────────────────
    user_id: str
    # session_id doubles as the LangGraph thread_id for MemorySaver.
    # Using the same ID means conversation memory is tied to the DB session.
    session_id: str

    # ── 2. User Input (set fresh each request) ─────────────────────────────────
    user_message: str
    # Target role the user is working toward: "AI Engineer", "Data Scientist", etc.
    target_role: str
    # Raw text extracted from uploaded PDF resume
    resume_text: str

    # ── 3. Agent Control (set by Supervisor) ──────────────────────────────────
    # Which agent to call next. The conditional router reads this field.
    next_agent: str
    # Human-readable explanation of WHY the supervisor chose this agent.
    # Logged to LangFuse for debugging routing decisions.
    routing_reasoning: str
    # When the user request needs MULTIPLE agents (e.g. "analyze my resume
    # AND generate interview questions"), the supervisor queues them here.
    # ISSUE-14 FIX: plain list with last-write-wins (NOT operator.add).
    # operator.add was causing the queue to grow on every state merge because
    # LangGraph concatenates the lists instead of replacing them — an agent
    # that completes and wants to pop itself off the queue by returning
    # agent_queue[1:] would instead get [original_queue] + [original_queue[1:]]
    # appended together, so callers stayed in the queue indefinitely.
    # With last-write-wins, each node's returned agent_queue fully replaces
    # the previous value, which is the correct pop-from-front behaviour.
    agent_queue: list[str]
    # Audit trail of every agent called in this session turn.
    # operator.add IS correct here — we want to accumulate, never replace.
    agents_called: Annotated[list[str], operator.add]
    # Flag set by supervisor when multiple agents are needed.
    is_multi_agent: bool

    # ── 4. Resume Agent Outputs ────────────────────────────────────────────────
    resume_analysis: dict[str, Any]
    # Structure expected:
    # {
    #   "ats_score": int,          # 0-100
    #   "extracted_skills": list,  # ["Python", "SQL", ...]
    #   "missing_skills": list,    # ["Docker", "Kubernetes", ...]
    #   "strengths": list,         # ["Strong ML background", ...]
    #   "suggestions": list,       # ["Add project metrics", ...]
    # }

    # ── 5. Skill Gap Agent Outputs ─────────────────────────────────────────────
    skill_gap_analysis: dict[str, Any]
    # Structure expected:
    # {
    #   "current_skills": list,
    #   "required_skills": list,
    #   "missing_skills": list,
    #   "priority_order": list,    # ordered from most to least urgent
    #   "time_estimates": dict,    # { "Docker": "2 weeks", ... }
    # }

    # ── 6. Interview Agent Outputs ─────────────────────────────────────────────
    interview_output: dict[str, Any]
    # Structure expected:
    # {
    #   "session_type": "technical" | "hr" | "coding",
    #   "questions": [
    #     { "question": str, "expected_answer": str, "difficulty": str }
    #   ]
    # }
    # Passed in by frontend / API to tell Interview Agent what to generate
    interview_type: str   # "technical" | "hr" | "coding"

    # ── 7. Quiz Agent Outputs ──────────────────────────────────────────────────
    quiz_output: dict[str, Any]
    # Structure expected:
    # {
    #   "topic": str,
    #   "questions": [
    #     {
    #       "question": str,
    #       "options": ["A", "B", "C", "D"],
    #       "correct_answer": str,
    #       "explanation": str
    #     }
    #   ]
    # }
    quiz_topic: str        # Input: what topic to quiz on
    quiz_difficulty: str   # Input: "easy" | "medium" | "hard"

    # ── 8. Study Planner Agent Outputs ────────────────────────────────────────
    study_plan_output: dict[str, Any]
    # Structure expected:
    # {
    #   "plan_type": "daily" | "weekly" | "monthly",
    #   "days": [
    #     { "day": "Monday", "date": "...", "tasks": [...] }
    #   ]
    # }
    plan_type: str            # Input: "daily" | "weekly" | "monthly"
    available_hours: float    # Input: study hours per day

    # ── 9. RAG Context ────────────────────────────────────────────────────────
    # Retrieved document chunks injected into each agent's prompt.
    # Each agent replaces this with its own query results before running.
    rag_context: list[str]

    # ── Phase 2 Inputs ────────────────────────────────────────────────────────
    # LinkedIn Optimization Agent inputs
    linkedin_headline: str        # Current LinkedIn headline text
    linkedin_about: str           # Current LinkedIn About/Summary section
    linkedin_experience: str      # Current experience section text
    linkedin_skills: list[str]    # Current skills list on LinkedIn

    # Project Recommendation Agent inputs
    experience_level: str         # "fresher" | "1-2 years" | "3-5 years" | "5+ years"
    time_available_weeks: int     # How many weeks available to build projects

    # Spoken English Agent inputs
    spoken_text: str              # The transcript / typed answer to evaluate
    english_context_type: str     # "interview_answer" | "self_intro" | "email" | "presentation"
    question_answered: str        # The question the user was answering (for structure eval)

    # ── Phase 2 Agent Outputs ─────────────────────────────────────────────────
    linkedin_output: dict[str, Any]
    # {
    #   "current_score": int,
    #   "optimized_score": int,
    #   "sections": { "headline": {...}, "about": {...}, ... },
    #   "keyword_density": {...}
    # }

    project_recommendations_output: dict[str, Any]
    # {
    #   "recommended_projects": [...],
    #   "portfolio_score": int,
    #   "projects_to_avoid": [...]
    # }

    english_output: dict[str, Any]
    # {
    #   "corrected_text": str,
    #   "scores": { "grammar": int, "fluency": int, ... "overall": int },
    #   "issues": [...],
    #   "star_compliance": {...},
    #   "practice_scripts": {...},
    #   "vocabulary_upgrades": [...]
    # }

    # ── Phase 3 Inputs ────────────────────────────────────────────────────────
    # Company Research Agent inputs
    company_name: str         # "Google", "Microsoft", "Zoho"

    # Internship Research Agent inputs
    education_level: str      # "B.Tech 2nd year", "MBA 1st year"
    college_tier: str         # "IIT/NIT", "Tier 2", "Tier 3"
    available_from: str       # "May 2025"

    # Wellness Agent inputs
    mood_message: str         # Free-text emotional check-in from user

    # ── Phase 3 Agent Outputs ─────────────────────────────────────────────────
    company_research_output: dict[str, Any]
    # {
    #   "company_name": str, "overview": str, "tech_stack": [...],
    #   "interview_style": str, "culture_values": [...],
    #   "known_questions": [...], "skill_alignment": {...},
    #   "prep_strategy": [...], "alignment_score": int
    # }

    internship_research_output: dict[str, Any]
    # {
    #   "recommended_companies": [...], "application_timeline": {...},
    #   "cover_letter_outline": str, "skill_gaps_for_internships": [...]
    # }

    wellness_output: dict[str, Any]
    # {
    #   "emotional_validation": str, "reframe": str,
    #   "next_single_action": str, "progress_acknowledgment": str,
    #   "burnout_risk": { "level": str, "signals": [...], "recommendation": str },
    #   "motivational_quote": str, "adjusted_study_plan": {...}
    # }

    # ── 10. Final Output ──────────────────────────────────────────────────────
    # The synthesized response assembled from all agent outputs.
    final_response: dict[str, Any]
    # Structure expected:
    # {
    #   "message": str,           # Human-readable summary
    #   "agent_outputs": dict,    # Raw outputs keyed by agent name
    #   "recommendations": list,  # Top action items
    # }

    # ── 11. Error Handling ────────────────────────────────────────────────────
    # If an agent fails, it writes here instead of crashing the graph.
    # The synthesizer checks this field and returns a graceful error response.
    error: str | None
    error_agent: str | None   # Which agent failed


# ── Initial state factory ──────────────────────────────────────────────────────
def create_initial_state(
    user_id: str,
    session_id: str,
    user_message: str,
    target_role: str = "",
    resume_text: str = "",
    interview_type: str = "technical",
    quiz_topic: str = "",
    quiz_difficulty: str = "medium",
    plan_type: str = "weekly",
    available_hours: float = 2.0,
    # Phase 2 inputs
    linkedin_headline: str = "",
    linkedin_about: str = "",
    linkedin_experience: str = "",
    linkedin_skills: list | None = None,
    experience_level: str = "fresher",
    time_available_weeks: int = 4,
    spoken_text: str = "",
    english_context_type: str = "interview_answer",
    question_answered: str = "",
    # Phase 3 inputs
    company_name: str = "",
    education_level: str = "",
    college_tier: str = "",
    available_from: str = "",
    mood_message: str = "",
) -> CareerCopilotState:
    """
    Factory function that creates a clean initial state for each request.

    Why a factory instead of dict literals in each route?
      - Single place to set defaults — change once, applies everywhere
      - Type-checked — IDEs catch typos in field names
      - Self-documenting — clearly shows what's required vs optional per request
    """
    return CareerCopilotState(
        user_id=user_id,
        session_id=session_id,
        user_message=user_message,
        target_role=target_role,
        resume_text=resume_text,
        interview_type=interview_type,
        quiz_topic=quiz_topic,
        quiz_difficulty=quiz_difficulty,
        plan_type=plan_type,
        available_hours=available_hours,
        # Phase 2 inputs
        linkedin_headline=linkedin_headline,
        linkedin_about=linkedin_about,
        linkedin_experience=linkedin_experience,
        linkedin_skills=linkedin_skills or [],
        experience_level=experience_level,
        time_available_weeks=time_available_weeks,
        spoken_text=spoken_text,
        english_context_type=english_context_type,
        question_answered=question_answered,
        # Controlled fields — always reset at start of each request
        next_agent="",
        routing_reasoning="",
        agent_queue=[],
        agents_called=[],
        is_multi_agent=False,
        rag_context=[],
        error=None,
        error_agent=None,
        # Phase 1 output fields — populated by agents
        resume_analysis={},
        skill_gap_analysis={},
        interview_output={},
        quiz_output={},
        study_plan_output={},
        # Phase 2 output fields
        linkedin_output={},
        project_recommendations_output={},
        english_output={},
        # Phase 3 inputs
        company_name=company_name,
        education_level=education_level,
        college_tier=college_tier,
        available_from=available_from,
        mood_message=mood_message,
        # Phase 3 output fields
        company_research_output={},
        internship_research_output={},
        wellness_output={},
        final_response={},
    )


# ── Agent name constants ───────────────────────────────────────────────────────
# Use these constants everywhere instead of raw strings to prevent typos.
# When you add Phase 2 agents, add them here and the router picks them up.

class AgentName:
    SUPERVISOR          = "supervisor"
    RESUME              = "resume_agent"
    SKILL_GAP           = "skill_gap_agent"
    INTERVIEW           = "interview_agent"
    QUIZ                = "quiz_agent"
    STUDY_PLANNER       = "study_planner_agent"
    SYNTHESIZER         = "response_synthesizer"

    # Phase 2 — implemented
    LINKEDIN            = "linkedin_agent"
    PROJECT_RECOMMEND   = "project_recommendation_agent"
    SPOKEN_ENGLISH      = "spoken_english_agent"

    # Phase 3 — implemented
    COMPANY_RESEARCH    = "company_research_agent"
    INTERNSHIP_RESEARCH = "internship_research_agent"
    WELLNESS            = "wellness_agent"

    # Future stubs
    MATERIAL            = "material_agent"
    CAREER_STRATEGY     = "career_strategy_agent"
    PROGRESS_TRACKER    = "progress_tracking_agent"

    # Special routing values
    END                 = "end"
    ERROR               = "error_handler"

    PHASE_1_AGENTS: list[str] = [
        RESUME, SKILL_GAP, INTERVIEW, QUIZ, STUDY_PLANNER,
    ]
    PHASE_2_AGENTS: list[str] = [
        LINKEDIN, PROJECT_RECOMMEND, SPOKEN_ENGLISH,
    ]
    PHASE_3_AGENTS: list[str] = [
        COMPANY_RESEARCH, INTERNSHIP_RESEARCH, WELLNESS,
    ]
    ALL_AGENTS: list[str] = PHASE_1_AGENTS + PHASE_2_AGENTS + PHASE_3_AGENTS
