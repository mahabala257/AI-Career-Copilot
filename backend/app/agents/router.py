"""
app/agents/router.py
─────────────────────
The Agent Router — the conditional edge logic in the LangGraph graph.

In LangGraph, a "conditional edge" is a function that:
  - Receives the current state
  - Returns the NAME of the next node to execute
  - Gets registered with add_conditional_edges()

The router is called AFTER the supervisor sets next_agent in state.
It also handles the multi-agent queue: when agent_queue is non-empty,
it routes to the next queued agent after each one completes.

Routing logic diagram:
─────────────────────
  After supervisor:
    state.next_agent = "resume_agent"
    state.agent_queue = ["skill_gap_agent", "study_planner_agent"]
    
    router() → "resume_agent"
    
  After resume_agent completes:
    state.agent_queue = ["skill_gap_agent", "study_planner_agent"]
    
    post_agent_router() → pops "skill_gap_agent" from queue
                       → sets next_agent = "skill_gap_agent"
                       → routes to "skill_gap_agent"
  
  After skill_gap_agent completes:
    state.agent_queue = ["study_planner_agent"]
    
    post_agent_router() → pops "study_planner_agent"
                       → routes to "study_planner_agent"
  
  After study_planner_agent completes:
    state.agent_queue = []
    
    post_agent_router() → queue empty → routes to "response_synthesizer"

Why two router functions?
  - route_from_supervisor():  called after supervisor, reads next_agent directly
  - route_after_agent():      called after each specialized agent completes,
                               checks the queue to decide what comes next
"""

import logging
from typing import Any

from app.agents.state import AgentName, CareerCopilotState

logger = logging.getLogger(__name__)


def route_from_supervisor(state: CareerCopilotState) -> str:
    """
    Conditional edge function called immediately after the supervisor node.

    Reads state.next_agent and returns the corresponding node name.
    LangGraph uses this return value to decide which node to execute next.

    The mapping must exactly match the node names registered in graph.py.
    If next_agent is empty or unknown, defaults to the synthesizer
    rather than crashing.
    """
    next_agent = state.get("next_agent", "")
    error = state.get("error")

    # If supervisor itself errored and set a fallback, still route it
    # (the fallback is a valid agent name set by the exception handlers)
    if not next_agent:
        logger.warning("[Router] next_agent is empty after supervisor — routing to synthesizer")
        return AgentName.SYNTHESIZER

    # Valid routes — Phase 1 + Phase 2
    valid_routes = {
        AgentName.RESUME:               AgentName.RESUME,
        AgentName.SKILL_GAP:            AgentName.SKILL_GAP,
        AgentName.INTERVIEW:            AgentName.INTERVIEW,
        AgentName.QUIZ:                 AgentName.QUIZ,
        AgentName.STUDY_PLANNER:        AgentName.STUDY_PLANNER,
        AgentName.LINKEDIN:             AgentName.LINKEDIN,
        AgentName.PROJECT_RECOMMEND:    AgentName.PROJECT_RECOMMEND,
        AgentName.SPOKEN_ENGLISH:       AgentName.SPOKEN_ENGLISH,
        AgentName.COMPANY_RESEARCH:     AgentName.COMPANY_RESEARCH,
        AgentName.INTERNSHIP_RESEARCH:  AgentName.INTERNSHIP_RESEARCH,
        AgentName.WELLNESS:             AgentName.WELLNESS,
    }

    route = valid_routes.get(next_agent)
    if route:
        logger.info(f"[Router] Supervisor → {route}")
        return route

    # Unknown agent name — log and go to synthesizer
    logger.warning(f"[Router] Unknown agent '{next_agent}' — routing to synthesizer")
    return AgentName.SYNTHESIZER


def route_after_agent(state: CareerCopilotState) -> str:
    """
    Conditional edge function called after EACH specialized agent completes.

    Checks the agent_queue. If agents remain in the queue, pops the next
    one. If empty, routes to the response synthesizer.

    Note: Because LangGraph state is immutable within a node call, we can't
    actually "pop" from the queue here — we just read the next item.
    The agent_queue is consumed by returning the next agent name; the queue
    itself shrinks because agents remove their own name when they complete
    (or the synthesizer handles remaining items).

    A cleaner approach for production: use a dedicated queue_manager node
    that explicitly manages the queue state. For Phase 1 this approach
    is sufficient.
    """
    agent_queue = state.get("agent_queue", [])
    agents_called = state.get("agents_called", [])

    # Find the next agent in the queue that hasn't been called yet
    for agent in agent_queue:
        if agent not in agents_called:
            logger.info(f"[Router] Queue → {agent} (remaining: {agent_queue})")
            return agent

    # All queued agents have been called (or queue was empty)
    logger.info("[Router] Queue exhausted → response_synthesizer")
    return AgentName.SYNTHESIZER


def route_after_synthesis(state: CareerCopilotState) -> str:
    """
    Conditional edge after the response synthesizer.
    Currently always ends the graph.
    In Phase 2, this could route to a feedback collector or score updater.
    """
    return "end"


# ── Routing decision logger ────────────────────────────────────────────────────
# Used by graph.py to log routing for LangFuse traces
def log_routing_decision(state: CareerCopilotState, from_node: str, to_node: str) -> None:
    logger.info(
        f"[Router] {from_node} → {to_node} | "
        f"user={state.get('user_id', '?')} | "
        f"message='{state.get('user_message', '')[:60]}'"
    )
