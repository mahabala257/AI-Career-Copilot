"""
app/main.py — FastAPI entry point with startup validation.
"""
import asyncio
import logging
import os
import sys
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

# ── Windows event-loop fix (must run before any event loop is created) ─────────
# psycopg's async driver (used by the LangGraph AsyncPostgresSaver checkpointer)
# cannot run on Windows' default ProactorEventLoop and raises:
#   "Psycopg cannot use the 'ProactorEventLoop' to run in async mode".
# Switching to the SelectorEventLoop policy makes the Postgres checkpointer work
# (persistent conversation memory). asyncpg — the app's main DB driver — runs
# fine on either loop, so this is safe.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _log_api_key_status() -> None:
    """Log masked API key status at startup to aid debugging."""
    groq_key = settings.groq_api_key.strip()
    google_key = settings.google_api_key.strip()

    def mask(k: str) -> str:
        return f"{k[:6]}...{k[-4:]}" if len(k) > 10 else ("(empty)" if not k else "****")

    logger.info(f"[LLM] GROQ_API_KEY   : {mask(groq_key)} (len={len(groq_key)})")
    logger.info(f"[LLM] GOOGLE_API_KEY : {mask(google_key)} (len={len(google_key)}) [fallback]")

    if not groq_key:
        logger.error(
            "[LLM] GROQ_API_KEY is empty! Get a free key at https://console.groq.com/keys "
            "and add it to your .env as GROQ_API_KEY=gsk_..."
        )
    elif groq_key.startswith("gsk_"):
        logger.info("[LLM] GROQ_API_KEY format looks valid ✓")
    else:
        logger.warning(f"[LLM] GROQ_API_KEY starts with '{groq_key[:4]}' — expected 'gsk_'")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version} [{settings.environment}]")

    _log_api_key_status()

    from app.db.database import check_db_connection
    db_ok = await check_db_connection()
    logger.info(f"[DB] {'OK' if db_ok else 'FAILED — check DATABASE_URL'}")

    # Ensure newer tables exist (idempotent; create_all only creates missing
    # tables and never alters/drops existing ones — safe without a migration).
    if db_ok:
        try:
            from app.db.database import Base, engine
            from app.models.phase4_models import Goal  # noqa: F401
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, tables=[Goal.__table__])
            logger.info("[DB] Ensured 'goals' table exists")
        except Exception as e:
            logger.warning(f"[DB] goals-table ensure failed (non-fatal): {e}")

    from app.agents.graph import initialise_graph
    await initialise_graph()

    os.makedirs(settings.upload_dir,    exist_ok=True)
    os.makedirs(settings.chromadb_path, exist_ok=True)

    try:
        from app.rag.ingestion.loader import get_ingestion_status, seed_all_collections
        status = get_ingestion_status()
        needs_seed = any(not v["seeded"] for v in status.values())
        if needs_seed:
            logger.info("[RAG] Collections empty — auto-seeding knowledge base...")
            results = seed_all_collections(force=False)
            seeded  = sum(r.upserted for r in results)
            logger.info(f"[RAG] Auto-seed complete: {seeded} documents ingested")
        else:
            total = sum(v["count"] for v in status.values())
            logger.info(f"[RAG] Collections ready: {total} total documents")
    except Exception as e:
        logger.warning(f"[RAG] Auto-seed failed (non-fatal): {e}")

    logger.info("Server ready ✓")
    yield

    from app.db.database import engine
    await engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Career Copilot — agentic career development platform",
        docs_url="/docs"  if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global error handling ──────────────────────────────────────────────────
    # Any unhandled error returns clean JSON (never an opaque 500 page). LLM
    # rate-limit errors get a friendly, actionable 503 so the UI can tell the
    # user to wait a moment instead of showing a scary failure.
    _RATE_HINTS = ("rate limit", "rate_limit", "ratelimit", "too many requests", "429", "quota")

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        text = str(exc).lower()
        if any(h in text for h in _RATE_HINTS):
            logger.warning(f"[RateLimit] {request.url.path}: {str(exc)[:160]}")
            return JSONResponse(
                status_code=503,
                content={"detail": "The AI service is busy right now (free-tier rate limit). "
                                   "Please wait ~30 seconds and try again."},
            )
        logger.error(f"[Unhandled] {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Something went wrong on our end. Please try again."},
        )

    # ── Per-IP rate limiting on write endpoints ────────────────────────────────
    # Sliding window: blocks runaway loops / abuse while staying generous for a
    # single user. In-memory (fine for single-process dev/demo). Auth routes are
    # excluded so the token-refresh flow is never throttled.
    _RL_WINDOW = 60          # seconds
    _RL_MAX = 40             # POST requests per minute per IP
    _rl_buckets: dict[str, deque] = defaultdict(deque)

    @app.middleware("http")
    async def rate_limiter(request: Request, call_next):
        path = request.url.path
        if request.method == "POST" and path.startswith("/api/") and not path.startswith("/api/auth/"):
            key = request.client.host if request.client else "anon"
            now = time.monotonic()
            dq = _rl_buckets[key]
            while dq and now - dq[0] > _RL_WINDOW:
                dq.popleft()
            if len(dq) >= _RL_MAX:
                # Add CORS headers manually so the browser can read this 429.
                headers = {}
                origin = request.headers.get("origin")
                if origin and origin in settings.cors_origins_list:
                    headers["Access-Control-Allow-Origin"] = origin
                    headers["Access-Control-Allow-Credentials"] = "true"
                return JSONResponse(
                    status_code=429,
                    content={"detail": "You're sending requests too quickly. Please wait a minute and try again."},
                    headers=headers,
                )
            dq.append(now)
        return await call_next(request)

    from app.api.routes.auth       import router as auth_router
    from app.api.routes.resume     import router as resume_router
    from app.api.routes.skills     import router as skills_router
    from app.api.routes.interview  import router as interview_router
    from app.api.routes.quiz       import router as quiz_router
    from app.api.routes.planner    import router as planner_router
    from app.api.routes.progress   import router as progress_router
    from app.api.routes.linkedin   import router as linkedin_router
    from app.api.routes.projects   import router as projects_router
    from app.api.routes.english    import router as english_router
    from app.api.routes.company    import router as company_router
    from app.api.routes.internship import router as internship_router
    from app.api.routes.wellness   import router as wellness_router
    from app.api.routes.chat       import router as chat_router
    from app.api.routes.goals      import router as goals_router
    from app.api.routes.notifications import router as notifications_router

    app.include_router(auth_router)
    app.include_router(resume_router)
    app.include_router(skills_router)
    app.include_router(interview_router)
    app.include_router(quiz_router)
    app.include_router(planner_router)
    app.include_router(progress_router)
    app.include_router(linkedin_router)
    app.include_router(projects_router)
    app.include_router(english_router)
    app.include_router(company_router)
    app.include_router(internship_router)
    app.include_router(wellness_router)
    app.include_router(chat_router)
    app.include_router(goals_router)
    app.include_router(notifications_router)

    @app.get("/", tags=["System"])
    async def root():
        return {"name": settings.app_name, "version": settings.app_version, "status": "running"}

    @app.get("/health", tags=["System"])
    async def health():
        from app.db.database import check_db_connection
        from app.rag.rag_pipeline import get_rag_health
        db_ok = await check_db_connection()
        rag   = await get_rag_health()
        return {
            "status":      "healthy" if db_ok else "degraded",
            "database":    "connected" if db_ok else "disconnected",
            "ai_service":  "configured" if settings.groq_api_key else "missing_key",
            "rag":         rag,
            "environment": settings.environment,
            "version":     settings.app_version,
        }

    return app


app = create_app()
