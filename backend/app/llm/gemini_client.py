"""
app/llm/gemini_client.py
─────────────────────────
Production Gemini client layer.

Why this file exists
─────────────────────
Every agent needs a Gemini LLM instance. If we created one inside each agent
module we would have duplicate configuration, no shared rate limiter (each agent
thinks it has full quota), no central retry policy, and no easy model switching.

This module gives the app ONE configured, shared instance per model variant,
created lazily and cached for the lifetime of the process.

Model strategy for AI Career Copilot
──────────────────────────────────────
  gemini-2.0-flash   → DEFAULT. Fast, cheap, strong instruction-following.
                       Free tier: 15 req/min, 1M tokens/day.
  gemini-1.5-pro     → Deep reasoning. Use for complex resume critique or
                       multi-step career strategy. Free tier: 2 req/min.
  gemini-1.5-flash-8b → Ultra-fast for high-volume simple tasks.

Rate limiting
──────────────
InMemoryRateLimiter uses a token bucket algorithm. We set 14 req/min
(just below the 15/min free tier limit) to leave headroom for retries.

Retry policy
─────────────
max_retries=3 handles 429 and 503 automatically via LangChain's built-in
retry wrapper. We do NOT retry 400/401/403 (key/prompt problems).
"""

import logging
from functools import lru_cache

from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings

logger = logging.getLogger(__name__)

# ── Model name constants ───────────────────────────────────────────────────────
GEMINI_FLASH    = "gemini-2.0-flash"
GEMINI_PRO      = "gemini-1.5-pro"
GEMINI_FLASH_8B = "gemini-1.5-flash-8b"
DEFAULT_MODEL   = GEMINI_FLASH


# ── Shared rate limiters ───────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _get_flash_rate_limiter() -> InMemoryRateLimiter:
    # 14 req/min keeps us safely under the 15/min free tier ceiling
    return InMemoryRateLimiter(
        requests_per_second=14 / 60,
        check_every_n_seconds=0.5,
        max_bucket_size=14,
    )

@lru_cache(maxsize=1)
def _get_pro_rate_limiter() -> InMemoryRateLimiter:
    # 1 req/min keeps us safely under the 2/min free tier ceiling
    return InMemoryRateLimiter(
        requests_per_second=1 / 60,
        check_every_n_seconds=1.0,
        max_bucket_size=2,
    )


# ── Client factories ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_gemini_flash() -> ChatGoogleGenerativeAI:
    """
    Gemini 2.0 Flash — primary LLM for all Phase 1 agents.
    Used by: Supervisor, Resume Agent, Skill Gap Agent, Study Planner Agent.
    temperature=0.3 keeps outputs structured and consistent.
    """
    _warn_if_no_key()
    logger.info(f"[Gemini] Initializing {GEMINI_FLASH}")
    return ChatGoogleGenerativeAI(
        model=GEMINI_FLASH,
        google_api_key=settings.google_api_key,
        temperature=0.3,
        max_output_tokens=4096,
        # Gemini has no native system role — LangChain converts SystemMessage
        # to a Human turn with a prefix Gemini understands equally well.
        convert_system_message_to_human=True,
        max_retries=3,
        rate_limiter=_get_flash_rate_limiter(),
    )


@lru_cache(maxsize=1)
def get_gemini_pro() -> ChatGoogleGenerativeAI:
    """
    Gemini 1.5 Pro — deep reasoning tasks only.
    Rate limit is strict (2 req/min free tier) — use sparingly.
    """
    _warn_if_no_key()
    logger.info(f"[Gemini] Initializing {GEMINI_PRO}")
    return ChatGoogleGenerativeAI(
        model=GEMINI_PRO,
        google_api_key=settings.google_api_key,
        temperature=0.2,
        max_output_tokens=8192,
        convert_system_message_to_human=True,
        max_retries=2,
        rate_limiter=_get_pro_rate_limiter(),
    )


@lru_cache(maxsize=1)
def get_gemini_flash_8b() -> ChatGoogleGenerativeAI:
    """Gemini 1.5 Flash 8B — ultra-fast for simple classification tasks."""
    _warn_if_no_key()
    return ChatGoogleGenerativeAI(
        model=GEMINI_FLASH_8B,
        google_api_key=settings.google_api_key,
        temperature=0.1,
        max_output_tokens=2048,
        convert_system_message_to_human=True,
        max_retries=3,
        rate_limiter=_get_flash_rate_limiter(),
    )


def get_gemini(model: str = DEFAULT_MODEL) -> ChatGoogleGenerativeAI:
    """
    Generic getter — choose model by name constant.
    Usage:  llm = get_gemini(GEMINI_PRO)
    """
    dispatch = {
        GEMINI_FLASH:    get_gemini_flash,
        GEMINI_PRO:      get_gemini_pro,
        GEMINI_FLASH_8B: get_gemini_flash_8b,
    }
    factory = dispatch.get(model)
    if factory is None:
        logger.warning(f"[Gemini] Unknown model '{model}', falling back to {DEFAULT_MODEL}")
        factory = get_gemini_flash
    return factory()


# ── Health check ───────────────────────────────────────────────────────────────
async def check_gemini_connection() -> dict:
    """
    Minimal connectivity test called at FastAPI startup.
    Returns a status dict included in the /health endpoint response.
    """
    if not settings.google_api_key:
        return {"status": "not_configured", "model": DEFAULT_MODEL}
    try:
        llm = get_gemini_flash()
        response = await llm.ainvoke("Reply with the single word: OK")
        text = response.content.strip()
        return {
            "status": "connected" if "ok" in text.lower() else "unexpected_response",
            "model": DEFAULT_MODEL,
            "response_preview": text[:50],
        }
    except Exception as e:
        return {"status": "error", "model": DEFAULT_MODEL, "error": str(e)[:100]}


def _warn_if_no_key() -> None:
    if not settings.google_api_key:
        logger.warning(
            "[Gemini] GOOGLE_API_KEY not set — LLM calls will fail. "
            "Add it to your .env file."
        )
