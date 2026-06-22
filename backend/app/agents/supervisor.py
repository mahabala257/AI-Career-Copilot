"""
app/agents/supervisor.py
─────────────────────────
The Supervisor Agent — the brain of the entire system.

Responsibilities
────────────────
  1. Parse the user's message and understand their intent
  2. Decide which agent (or agents) to invoke
  3. Set next_agent in state so the router knows where to send the graph
  4. Build an agent_queue when multiple agents are needed
  5. Provide reasoning for the routing decision (logged to LangFuse)

Why Gemini 1.5 Pro for the Supervisor?
  - The routing decision is the most critical step — wrong routing wastes
    time, burns tokens on the wrong agent, and gives a bad user experience
  - Gemini 1.5 Pro has the best instruction-following among free-tier models
  - Large context window means it can consider full conversation history

Supervisor prompt design
─────────────────────────
The prompt uses strict JSON output format so we can reliably parse the
routing decision without fragile regex. The model is instructed to:
  - Always return valid JSON (no markdown fences, no extra text)
  - Choose from the exact agent names in AgentName constants
  - Set needs_multiple=true when the request spans multiple agents
  - Provide a human-readable reasoning string for debugging

Error handling
──────────────
If Gemini returns malformed JSON or fails entirely, the supervisor falls
back to keyword-based routing. This ensures the system degrades gracefully
rather than crashing — a user who uploads a resume still gets a response
even if the LLM routing call fails.
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentName, CareerCopilotState
# FIX-9: Changed from get_gemini_pro to get_gemini_flash.
# The supervisor runs on every request. gemini-1.5-pro has a 2 req/min free
# tier limit, so under any real load the system always fell back to keyword
# routing, making the LLM-based routing non-functional.
# gemini-2.0-flash has a 15 req/min limit and strong instruction-following —
# more than sufficient for routing decisions.
from app.llm.gemini_client import get_gemini_flash

logger = logging.getLogger(__name__)

# ── Supervisor system prompt ───────────────────────────────────────────────────
# This is the most important prompt in the entire system.
# It defines the routing intelligence of the Supervisor Agent.
SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent for AI Career Copilot, 
an intelligent platform that helps students and job seekers grow their careers.

Your ONLY job is to analyze the user's message and decide which specialized 
agent(s) should handle the request.

Available agents and what they do:
─────────────────────────────────
Phase 1 agents:
- resume_agent:                Analyze resume PDFs, ATS scoring, extract skills, improvement suggestions
- skill_gap_agent:             Compare user's current skills vs target role requirements, find gaps
- interview_agent:             Generate HR, technical, or coding interview questions
- quiz_agent:                  Generate MCQ quizzes on technical topics, evaluate answers, find weak areas
- study_planner_agent:         Create daily/weekly/monthly study plans based on skill gaps

Phase 2 agents:
- linkedin_agent:              Optimize LinkedIn headline, About section, experience bullets, and skills for a target role
- project_recommendation_agent: Recommend specific portfolio projects based on skill gaps and target role
- spoken_english_agent:        Evaluate spoken/written English for interviews; fix grammar, filler words, STAR structure; generate practice scripts

Phase 3 agents:
- company_research_agent:      Research a specific target company: tech stack, interview process, culture, known questions, prep strategy
- internship_research_agent:   Recommend internship programs, application timelines, and skill prep for students based on education level and college tier
- wellness_agent:               Provide emotional support, burnout detection, and motivation during job search/preparation; NEVER provides therapy, always redirects serious concerns to professional help

Routing rules:
─────────────
1. Choose the SINGLE most relevant agent if the request is focused.
2. Choose MULTIPLE agents if the request spans several areas.
3. For resume uploads → always use resume_agent.
4. For skill gap questions → always use skill_gap_agent.
5. For interview prep → always use interview_agent.
6. For quizzes/tests → always use quiz_agent.
7. For study schedules/plans → always use study_planner_agent.
8. For LinkedIn profile optimization → always use linkedin_agent.
9. For project ideas or portfolio advice → always use project_recommendation_agent.
10. For English evaluation, grammar, filler words, STAR format, self-intro, practice scripts → always use spoken_english_agent.
11. For researching a specific company, interview process, or "prepare me for [Company]" → always use company_research_agent.
12. For internship search, campus placement, "internship for B.Tech student" → always use internship_research_agent.
13. For emotional check-ins, feeling discouraged, burnout, stress, motivation → always use wellness_agent.
14. For broad requests like "help me become an AI engineer" → use multiple agents:
    [skill_gap_agent, resume_agent, study_planner_agent]
15. For "prepare me for interviews and fix my English" → use multiple:
    [interview_agent, spoken_english_agent]
16. For "I have an interview at Google next week" → use multiple:
    [company_research_agent, interview_agent]
17. For "I keep failing interviews and want to give up" → use multiple:
    [wellness_agent, interview_agent]

You MUST respond with ONLY a valid JSON object. No markdown, no explanation outside the JSON.

Response format:
{
  "primary_agent": "<agent_name>",
  "additional_agents": [],
  "needs_multiple": false,
  "reasoning": "<why you chose this agent, 1-2 sentences>",
  "user_intent": "<brief summary of what the user wants>"
}

If multiple agents needed:
{
  "primary_agent": "skill_gap_agent",
  "additional_agents": ["resume_agent", "study_planner_agent"],
  "needs_multiple": true,
  "reasoning": "User wants a full career plan which requires skill analysis, resume review, and study scheduling",
  "user_intent": "Full career development plan for AI Engineer role"
}
"""


def _keyword_fallback_routing(user_message: str) -> str:
    """
    Fallback routing when Gemini fails or returns invalid JSON.

    Simple keyword matching — not as smart as LLM routing, but ensures
    the system always returns something useful rather than crashing.

    Returns the agent name string.
    """
    msg_lower = user_message.lower()

    keyword_map = {
        AgentName.RESUME: [
            "resume", "cv", "ats", "application", "job application",
            "upload", "parse resume", "review my resume"
        ],
        AgentName.SKILL_GAP: [
            "skill", "skills", "gap", "missing", "learn", "need to know",
            "what skills", "requirements", "tech stack"
        ],
        AgentName.INTERVIEW: [
            "interview", "questions", "hr", "technical interview",
            "coding interview", "mock interview", "prepare for interview"
        ],
        AgentName.QUIZ: [
            "quiz", "test", "mcq", "assess", "evaluate", "knowledge check",
            "practice questions", "exam"
        ],
        AgentName.STUDY_PLANNER: [
            "study", "plan", "schedule", "roadmap", "learning plan",
            "weekly", "daily", "monthly", "how long", "timeline"
        ],
        AgentName.LINKEDIN: [
            "linkedin", "headline", "about section", "optimize profile",
            "linkedin profile", "profile summary", "recruiter"
        ],
        AgentName.PROJECT_RECOMMEND: [
            "project", "portfolio", "what should i build", "project ideas",
            "github", "side project", "project recommendation"
        ],
        AgentName.SPOKEN_ENGLISH: [
            "english", "grammar", "filler", "spoken", "speech", "self intro",
            "tell me about yourself", "practice script", "star format",
            "how do i sound", "improve my answer", "evaluate my response"
        ],
        AgentName.COMPANY_RESEARCH: [
            "research company", "tell me about google", "tell me about microsoft",
            "prepare for", "company interview", "tech stack of", "interview process at",
            "what's it like at", "company culture", "glassdoor"
        ],
        AgentName.INTERNSHIP_RESEARCH: [
            "internship", "intern", "campus placement", "summer internship",
            "college placement", "off-campus", "ppo", "stipend"
        ],
        AgentName.WELLNESS: [
            "feeling discouraged", "want to give up", "failed interview",
            "stressed", "burnout", "motivate me", "feeling stuck",
            "demotivated", "is this worth it", "feeling down", "anxious",
            "overwhelmed", "lost hope", "exhausted"
        ],
    }

    for agent, keywords in keyword_map.items():
        if any(kw in msg_lower for kw in keywords):
            logger.info(f"[Supervisor] Fallback routing → {agent}")
            return agent

    # Default: skill gap is the most generally useful starting point
    logger.info("[Supervisor] No keyword match — defaulting to skill_gap_agent")
    return AgentName.SKILL_GAP


def _parse_supervisor_response(raw: str) -> dict[str, Any]:
    """
    Parse the JSON response from Gemini.

    Handles edge cases:
      - Gemini sometimes wraps JSON in ```json ... ``` markdown blocks
      - Sometimes adds a brief explanation before the JSON
      - Rarely returns completely invalid JSON
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = cleaned.rstrip("```").strip()

    # Find the JSON object even if there's surrounding text
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)

    return json.loads(cleaned)


async def supervisor_node(state: CareerCopilotState) -> dict[str, Any]:
    """
    The Supervisor Agent LangGraph node.

    This function is registered as a node in the StateGraph.
    LangGraph calls it with the current state and expects a dict back
    containing only the fields this node wants to update.

    Flow:
      1. Build prompt from state (user message + conversation context)
      2. Call Gemini for routing decision
      3. Parse JSON response
      4. Update state: next_agent, agent_queue, routing_reasoning, is_multi_agent
      5. On failure: use keyword fallback, log error

    Returns a partial state dict — only the fields being updated.
    """
    logger.info(
        f"[Supervisor] Processing message for user {state.get('user_id', 'unknown')}"
    )
    logger.info(f"[Supervisor] User message: {state.get('user_message', '')[:100]}")

    user_message = state.get("user_message", "")
    target_role = state.get("target_role", "")
    resume_text = state.get("resume_text", "")

    # ── Build user context message ─────────────────────────────────────────────
    # Give Gemini all the context it needs to make a good routing decision.
    context_parts = [f"User message: {user_message}"]

    if target_role:
        context_parts.append(f"Target role: {target_role}")

    if resume_text:
        # Don't send full resume — just signal that one is available
        context_parts.append("Resume: [Resume PDF has been uploaded and parsed]")

    if state.get("resume_analysis"):
        context_parts.append("Previous resume analysis: [Available in context]")

    if state.get("skill_gap_analysis"):
        context_parts.append("Previous skill gap analysis: [Available in context]")

    user_context = "\n".join(context_parts)

    # ── Call Gemini ────────────────────────────────────────────────────────────
    try:
        llm = get_gemini_flash()   # FIX-9: was get_gemini_pro()
        response = await llm.ainvoke([
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=user_context),
        ])

        raw_content = response.content
        logger.debug(f"[Supervisor] Raw Gemini response: {raw_content[:300]}")

        # Parse the routing decision
        parsed = _parse_supervisor_response(raw_content)

        primary_agent = parsed.get("primary_agent", "")
        additional_agents = parsed.get("additional_agents", [])
        needs_multiple = parsed.get("needs_multiple", False)
        reasoning = parsed.get("reasoning", "")
        user_intent = parsed.get("user_intent", "")

        # Validate the agent name is one we actually support
        all_valid_agents = AgentName.ALL_AGENTS
        if primary_agent not in all_valid_agents:
            logger.warning(
                f"[Supervisor] Gemini returned unknown agent '{primary_agent}', "
                f"falling back to keyword routing"
            )
            primary_agent = _keyword_fallback_routing(user_message)
            additional_agents = []
            needs_multiple = False
            reasoning = f"Fallback: keyword routing after invalid LLM response"

        # Filter additional_agents to only valid ones
        additional_agents = [
            a for a in additional_agents if a in all_valid_agents
        ]

        logger.info(
            f"[Supervisor] Routing decision: primary={primary_agent}, "
            f"additional={additional_agents}, multi={needs_multiple}"
        )
        logger.info(f"[Supervisor] Reasoning: {reasoning}")

        return {
            "next_agent": primary_agent,
            # agent_queue holds remaining agents after the primary one.
            # The router pops from this queue after each agent completes.
            "agent_queue": additional_agents,
            "is_multi_agent": needs_multiple,
            "routing_reasoning": reasoning,
            # Track that supervisor was called
            "agents_called": [AgentName.SUPERVISOR],
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Supervisor] JSON parse error: {e}")
        fallback = _keyword_fallback_routing(user_message)
        return {
            "next_agent": fallback,
            "agent_queue": [],
            "is_multi_agent": False,
            "routing_reasoning": f"JSON parse error, used keyword fallback",
            "agents_called": [AgentName.SUPERVISOR],
            "error": f"Supervisor JSON parse error: {e}",
            "error_agent": AgentName.SUPERVISOR,
        }

    except Exception as e:
        logger.error(f"[Supervisor] Unexpected error: {e}", exc_info=True)
        fallback = _keyword_fallback_routing(user_message)
        return {
            "next_agent": fallback,
            "agent_queue": [],
            "is_multi_agent": False,
            "routing_reasoning": f"LLM error, used keyword fallback: {str(e)[:100]}",
            "agents_called": [AgentName.SUPERVISOR],
            "error": f"Supervisor error: {str(e)[:200]}",
            "error_agent": AgentName.SUPERVISOR,
        }
