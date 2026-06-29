"""
app/llm/groq_client.py
───────────────────────
Groq LLM client setup for speed-sensitive agents.

Why Groq for Interview, Quiz, and Study Planner agents?
  - Groq runs LLaMA 3 70B at ~300 tokens/second — roughly 10x faster than
    hosted Gemini for the same model size
  - Interview questions, MCQs, and study plans are high-volume, latency-
    sensitive outputs where the user is waiting in real time
  - Gemini is reserved for reasoning-heavy tasks (routing, resume analysis,
    skill gap analysis) where quality matters more than speed

Groq models available (as of 2024):
  llama3-70b-8192  — best quality, 8k context
  llama3-8b-8192   — fastest, slightly lower quality
  mixtral-8x7b     — good for structured output tasks
"""

import logging
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_groq_llm():
    """
    Returns the Groq LLaMA 3 70B client (singleton).

    Used by:
      - Interview Agent (generates questions fast)
      - Quiz Agent (generates MCQs fast)
      - Study Planner Agent (generates structured plans fast)

    We import ChatGroq lazily so the server starts even if langchain-groq
    isn't installed yet — prevents hard crashes in environments where only
    Gemini is configured.
    """
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        logger.error(
            "[Groq] langchain-groq not installed. "
            "Run: pip install langchain-groq"
        )
        raise

    if not settings.groq_api_key:
        logger.warning(
            "[Groq] GROQ_API_KEY not set — Groq LLM calls will fail. "
            "Set it in your .env file."
        )

    return ChatGroq(
        model=settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=0.4,
        # Groq supports up to 8192 tokens context for llama3-70b
        max_tokens=4096,
    )
