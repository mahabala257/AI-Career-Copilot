"""
app/main.py
────────────
FastAPI application — production entry point.
Step 9: All routes registered, RAG auto-seeds on startup.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.app_name} v{settings.app_version} [{settings.environment}]")

    # DB check
    from app.db.database import check_db_connection
    db_ok = await check_db_connection()
    logger.info(f"[DB] {'OK' if db_ok else 'FAILED — check DATABASE_URL'}")

    # BUG-05 FIX: compile the LangGraph graph with the persistent postgres checkpointer.
    # Must run after the DB is confirmed reachable so AsyncPostgresSaver can connect.
    from app.agents.graph import initialise_graph
    await initialise_graph()

    # Upload + ChromaDB dirs
    os.makedirs(settings.upload_dir,    exist_ok=True)
    os.makedirs(settings.chromadb_path, exist_ok=True)

    # Auto-seed ChromaDB if collections are empty
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
        logger.warning(f"[RAG] Auto-seed failed (will retry on next restart): {e}")

    logger.info("Server ready ✓")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────────
    from app.db.database import engine
    await engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Agentic AI career development platform — LangGraph + Gemini + ChromaDB",
        docs_url="/docs"  if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────────────────────
    from app.api.routes.auth      import router as auth_router
    from app.api.routes.resume    import router as resume_router
    from app.api.routes.skills    import router as skills_router
    from app.api.routes.interview import router as interview_router
    from app.api.routes.quiz      import router as quiz_router
    from app.api.routes.planner   import router as planner_router
    from app.api.routes.progress  import router as progress_router
    from app.api.routes.linkedin  import router as linkedin_router
    from app.api.routes.projects  import router as projects_router
    from app.api.routes.english   import router as english_router
    from app.api.routes.company   import router as company_router
    from app.api.routes.internship import router as internship_router
    from app.api.routes.wellness  import router as wellness_router

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

    # ── System endpoints ────────────────────────────────────────────────────────
    @app.get("/", tags=["System"])
    async def root():
        return {"name": settings.app_name, "version": settings.app_version, "status": "running", "docs": "/docs"}

    @app.get("/health", tags=["System"])
    async def health():
        from app.db.database import check_db_connection
        from app.rag.rag_pipeline import get_rag_health
        db_ok  = await check_db_connection()
        rag    = await get_rag_health()
        return {
            "status":      "healthy" if db_ok else "degraded",
            "database":    "connected" if db_ok else "disconnected",
            "rag":         rag,
            "environment": settings.environment,
            "version":     settings.app_version,
        }

    return app


app = create_app()
