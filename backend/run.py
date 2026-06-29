"""
run.py — backend launcher (recommended on Windows).

Why this file exists
────────────────────
psycopg's async driver (used by the LangGraph AsyncPostgresSaver checkpointer
for persistent conversation memory) cannot run on Windows' default
ProactorEventLoop. `python -m uvicorn app.main:app` creates its event loop
BEFORE importing the app, so setting the loop policy inside app/main.py is too
late and the checkpointer falls back to in-memory storage.

This launcher sets the SelectorEventLoop policy FIRST, then starts uvicorn, so
the Postgres checkpointer works and conversation memory survives restarts.

Usage
─────
    cd backend
    venv\\Scripts\\activate
    python run.py

(Plain `uvicorn app.main:app --reload` still works — it just uses in-memory
conversation checkpoints that reset on restart.)
"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.is_development,
        # uvicorn must not install its own loop, or it would override the
        # SelectorEventLoop policy we just set above.
        loop="asyncio",
    )
