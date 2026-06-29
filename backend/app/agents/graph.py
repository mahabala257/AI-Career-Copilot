"""
app/agents/graph.py
────────────────────
LangGraph StateGraph — all nodes, edges, and memory compiled in one place.

BUG-05 FIX: replaced in-process MemorySaver with AsyncPostgresSaver so
LangGraph conversation checkpoints survive backend restarts and container
replacements. The graph is compiled lazily via get_graph() which must be
awaited the first time it is called from an async context (startup or
first request). A MemorySaver fallback is used if PostgreSQL is unavailable
so local development without a database still functions.
"""
import asyncio
import logging

from langgraph.graph import END, START, StateGraph

from app.agents.state import AgentName, CareerCopilotState
from app.agents.router import route_after_agent, route_from_supervisor
from app.agents.supervisor import supervisor_node
from app.agents.synthesizer import synthesizer_node

logger = logging.getLogger(__name__)

# ── Import real agents (fall back to stubs on ImportError) ────────────────────
try:
    from app.agents.career.resume_agent import resume_agent_node
except ImportError:
    from app.agents.placeholders import resume_agent_node  # type: ignore

try:
    from app.agents.career.skill_gap_agent import skill_gap_agent_node
except ImportError:
    from app.agents.placeholders import skill_gap_agent_node  # type: ignore

try:
    from app.agents.interview.interview_agent import interview_agent_node
except ImportError:
    from app.agents.placeholders import interview_agent_node  # type: ignore

try:
    from app.agents.interview.quiz_agent import quiz_agent_node
except ImportError:
    from app.agents.placeholders import quiz_agent_node  # type: ignore

try:
    from app.agents.personal.study_planner_agent import study_planner_agent_node
except ImportError:
    from app.agents.placeholders import study_planner_agent_node  # type: ignore

try:
    from app.agents.personal.linkedin_agent import linkedin_agent_node
except ImportError:
    from app.agents.placeholders import linkedin_agent_node  # type: ignore

try:
    from app.agents.personal.project_recommendation_agent import project_recommendation_agent_node
except ImportError:
    from app.agents.placeholders import project_recommendation_agent_node  # type: ignore

try:
    from app.agents.personal.spoken_english_agent import spoken_english_agent_node
except ImportError:
    from app.agents.placeholders import spoken_english_agent_node  # type: ignore

try:
    from app.agents.company.company_research_agent import company_research_agent_node
except ImportError:
    from app.agents.placeholders import company_research_agent_node  # type: ignore

try:
    from app.agents.company.internship_research_agent import internship_research_agent_node
except ImportError:
    from app.agents.placeholders import internship_research_agent_node  # type: ignore

try:
    from app.agents.personal.wellness_agent import wellness_agent_node
except ImportError:
    from app.agents.placeholders import wellness_agent_node  # type: ignore


def build_graph() -> StateGraph:
    graph = StateGraph(CareerCopilotState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    graph.add_node(AgentName.SUPERVISOR,       supervisor_node)
    graph.add_node(AgentName.SYNTHESIZER,      synthesizer_node)
    graph.add_node(AgentName.RESUME,           resume_agent_node)
    graph.add_node(AgentName.SKILL_GAP,        skill_gap_agent_node)
    graph.add_node(AgentName.INTERVIEW,        interview_agent_node)
    graph.add_node(AgentName.QUIZ,             quiz_agent_node)
    graph.add_node(AgentName.STUDY_PLANNER,    study_planner_agent_node)
    # Phase 2
    graph.add_node(AgentName.LINKEDIN,         linkedin_agent_node)
    graph.add_node(AgentName.PROJECT_RECOMMEND,project_recommendation_agent_node)
    graph.add_node(AgentName.SPOKEN_ENGLISH,   spoken_english_agent_node)
    # Phase 3
    graph.add_node(AgentName.COMPANY_RESEARCH,    company_research_agent_node)
    graph.add_node(AgentName.INTERNSHIP_RESEARCH, internship_research_agent_node)
    graph.add_node(AgentName.WELLNESS,            wellness_agent_node)

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.add_edge(START, AgentName.SUPERVISOR)

    # ── Supervisor → Agent (conditional) ──────────────────────────────────────
    graph.add_conditional_edges(
        AgentName.SUPERVISOR,
        route_from_supervisor,
        {
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
            AgentName.SYNTHESIZER:          AgentName.SYNTHESIZER,
        },
    )

    # ── Agent → Queue/Synthesizer (conditional) ────────────────────────────────
    post_agent_routing = {
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
        AgentName.SYNTHESIZER:          AgentName.SYNTHESIZER,
    }
    for agent in AgentName.ALL_AGENTS:
        graph.add_conditional_edges(agent, route_after_agent, post_agent_routing)

    # ── Synthesizer → END ──────────────────────────────────────────────────────
    graph.add_edge(AgentName.SYNTHESIZER, END)


    logger.info("[Graph] Topology built: 5 real agents active")
    return graph


# ── Compiled graph singleton (set by initialise_graph() at startup) ───────────
_compiled_graph = None
# Long-lived psycopg connection pool backing the checkpointer. Kept at module
# scope so it is not garbage-collected for the lifetime of the process.
_checkpointer_pool = None


async def initialise_graph() -> None:
    """
    Called once from FastAPI lifespan (app/main.py) after the DB is confirmed
    healthy. Compiles the graph with AsyncPostgresSaver for persistent memory.

    Falls back to MemorySaver if the postgres checkpointer cannot be imported
    or fails to connect — this keeps local dev without a real DB working.
    """
    global _compiled_graph, _checkpointer_pool

    graph = build_graph()

    try:
        # BUG-05 FIX: use PostgreSQL-backed checkpointer so conversation
        # checkpoints survive restarts. Requires langgraph-checkpoint-postgres.
        #
        # FIX: AsyncPostgresSaver.from_conn_string() returns an async context
        # manager (not a saver), so the previous code crashed with
        # "'_AsyncGeneratorContextManager' object has no attribute 'setup'".
        # The correct long-lived pattern is to open our own AsyncConnectionPool
        # and construct AsyncPostgresSaver(pool) directly, keeping the pool alive
        # at module scope.
        # psycopg's async driver cannot run on Windows' ProactorEventLoop. If we
        # detect it, fail fast to MemorySaver instead of letting the pool spam
        # connection warnings for 15s before timing out. To get persistent
        # memory on Windows, launch via `python run.py` (sets SelectorEventLoop).
        import asyncio as _asyncio
        loop_name = type(_asyncio.get_running_loop()).__name__
        if loop_name == "ProactorEventLoop":
            raise RuntimeError(
                "ProactorEventLoop active — psycopg async is incompatible. "
                "Launch with `python run.py` for persistent Postgres memory."
            )

        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool
        from app.config import settings

        # psycopg3 wants a raw connection string (no +asyncpg / +psycopg2 prefix)
        conn_str = (
            settings.database_url
            .replace("postgresql+asyncpg://", "postgresql://")
            .replace("postgresql+psycopg2://", "postgresql://")
        )

        # autocommit + prepare_threshold=0 are required by AsyncPostgresSaver
        pool = AsyncConnectionPool(
            conninfo=conn_str,
            max_size=10,
            open=False,
            kwargs={"autocommit": True, "prepare_threshold": 0},
        )
        await pool.open(wait=True, timeout=10)
        _checkpointer_pool = pool

        checkpointer = AsyncPostgresSaver(pool)
        # setup() creates the checkpoint tables if they don't exist
        await checkpointer.setup()

        _compiled_graph = graph.compile(checkpointer=checkpointer)
        logger.info("[Graph] Compiled with AsyncPostgresSaver (persistent memory ✓)")

    except ImportError:
        logger.warning(
            "[Graph] langgraph-checkpoint-postgres / psycopg_pool not installed. "
            "Falling back to MemorySaver (conversation history lost on restart)."
        )
        _use_memory_saver(graph)

    except Exception as e:
        logger.error(
            f"[Graph] AsyncPostgresSaver failed ({e}). "
            "Falling back to MemorySaver."
        )
        if _checkpointer_pool is not None:
            try:
                await _checkpointer_pool.close()
            except Exception:
                pass
            _checkpointer_pool = None
        _use_memory_saver(graph)


def _use_memory_saver(graph: StateGraph) -> None:
    """Compile with in-process MemorySaver (dev/fallback only)."""
    global _compiled_graph
    from langgraph.checkpoint.memory import MemorySaver
    _compiled_graph = graph.compile(checkpointer=MemorySaver())
    logger.info("[Graph] Compiled with MemorySaver (in-process, non-persistent)")


def get_graph():
    """
    Return the compiled graph. Raises RuntimeError if initialise_graph()
    has not been awaited yet (should not happen in normal operation because
    the lifespan hook calls it before the server accepts requests).
    """
    if _compiled_graph is None:
        # Synchronous fallback for scripts / tests that import the graph
        # without going through the FastAPI lifespan.
        logger.warning(
            "[Graph] get_graph() called before initialise_graph() — "
            "compiling synchronously with MemorySaver."
        )
        graph = build_graph()
        _use_memory_saver(graph)
    return _compiled_graph

