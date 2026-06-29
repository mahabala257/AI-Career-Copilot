"""
app/llm/gemini_client.py
─────────────────────────
AI LLM client — rerouted to Groq (llama-3.3-70b-versatile).

WHY: Google AI Studio free-tier quota (429 RESOURCE_EXHAUSTED) blocks Gemini.
Groq's free tier is more generous and the API is fully compatible with
the same .invoke()/.ainvoke() → .content call pattern all agents use.

TO SWITCH BACK TO GEMINI LATER: restore a ChatGoogleGenerativeAI version
of get_gemini_flash/pro/flash_8b once your Google Cloud billing is enabled.
No agent files need to change either way — only this file.
"""

import asyncio
import logging
import time
from functools import lru_cache
from threading import Lock
from typing import Optional

from groq import Groq, AsyncGroq

from app.config import settings

logger = logging.getLogger(__name__)

# ── Model constants (names kept for import compatibility) ─────────────────────
# NOTE: switched to llama-3.1-8b-instant because the free-tier daily token limit
# (TPD) on llama-3.3-70b-versatile is only 100K/day and was being exhausted
# during development. The 8b-instant model has a separate, much larger free
# daily budget and is faster — ideal for testing the full app without hitting
# the wall. To restore higher answer quality later (with a paid/Dev-tier Groq
# key or a fresh quota), set these back to "llama-3.3-70b-versatile".
GEMINI_FLASH    = "llama-3.1-8b-instant"
GEMINI_PRO      = "llama-3.1-8b-instant"
GEMINI_FLASH_8B = "llama-3.1-8b-instant"
DEFAULT_MODEL   = GEMINI_FLASH

_RETRYABLE_HINTS     = ("429", "503", "rate limit", "unavailable", "overloaded")
_NON_RETRYABLE_HINTS = ("400", "401", "403", "api key not valid", "invalid argument")


class _TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, requests_per_minute: float, max_bucket_size: int):
        self.rate_per_second = requests_per_minute / 60.0
        self.max_tokens = max_bucket_size
        self.tokens = float(max_bucket_size)
        self.last_refill = time.monotonic()
        self._lock = Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate_per_second)
        self.last_refill = now

    def acquire(self) -> None:
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate_per_second
            time.sleep(min(wait, 0.5))

    async def aacquire(self) -> None:
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate_per_second
            await asyncio.sleep(min(wait, 0.5))


@lru_cache(maxsize=1)
def _get_flash_rate_limiter() -> _TokenBucket:
    return _TokenBucket(requests_per_minute=25, max_bucket_size=25)

@lru_cache(maxsize=1)
def _get_pro_rate_limiter() -> _TokenBucket:
    return _TokenBucket(requests_per_minute=10, max_bucket_size=10)


class _SimpleResponse:
    """Matches LangChain AIMessage interface: .content"""
    def __init__(self, content: str):
        self.content = content


class GeminiChatModel:
    """
    Thin Groq adapter. Accepts strings or LangChain-style message lists.
    Exposes .invoke() and .ainvoke() → _SimpleResponse with .content
    so all existing agent code works unchanged.
    """

    def __init__(self, model: str, api_key: str, temperature: float,
                 max_output_tokens: int, rate_limiter: _TokenBucket,
                 max_retries: int = 3):
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.rate_limiter = rate_limiter
        self.max_retries = max_retries
        self._client  = Groq(api_key=api_key)
        self._aclient = AsyncGroq(api_key=api_key)

    def _to_messages(self, messages) -> list[dict]:
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        out = []
        for m in messages:
            role    = getattr(m, "type", None) or (m.get("role") if isinstance(m, dict) else None) or "user"
            content = getattr(m, "content", None) if not isinstance(m, dict) else m.get("content", "")
            if role == "human":   role = "user"
            elif role == "ai":    role = "assistant"
            elif role not in ("system", "user", "assistant"): role = "user"
            out.append({"role": role, "content": str(content)})
        return out

    def _retryable(self, err: Exception) -> bool:
        msg = str(err).lower()
        if any(h in msg for h in _NON_RETRYABLE_HINTS): return False
        return any(h in msg for h in _RETRYABLE_HINTS)

    def invoke(self, messages) -> _SimpleResponse:
        msgs = self._to_messages(messages)
        last: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            self.rate_limiter.acquire()
            try:
                r = self._client.chat.completions.create(
                    model=self.model, messages=msgs,
                    temperature=self.temperature, max_tokens=self.max_output_tokens,
                )
                return _SimpleResponse(r.choices[0].message.content or "")
            except Exception as e:
                last = e
                if not self._retryable(e) or attempt == self.max_retries:
                    logger.error(f"[LLM] Call failed (attempt {attempt+1}): {e}")
                    raise
                logger.warning(f"[LLM] Retrying in {2**attempt}s: {e}")
                time.sleep(2 ** attempt)
        raise last  # type: ignore

    async def ainvoke(self, messages) -> _SimpleResponse:
        msgs = self._to_messages(messages)
        last: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            await self.rate_limiter.aacquire()
            try:
                r = await self._aclient.chat.completions.create(
                    model=self.model, messages=msgs,
                    temperature=self.temperature, max_tokens=self.max_output_tokens,
                )
                return _SimpleResponse(r.choices[0].message.content or "")
            except Exception as e:
                last = e
                if not self._retryable(e) or attempt == self.max_retries:
                    logger.error(f"[LLM] Async call failed (attempt {attempt+1}): {e}")
                    raise
                logger.warning(f"[LLM] Retrying in {2**attempt}s: {e}")
                await asyncio.sleep(2 ** attempt)
        raise last  # type: ignore


# ── Factories (same names as before — all agents import these) ────────────────

@lru_cache(maxsize=1)
def get_gemini_flash() -> GeminiChatModel:
    _warn_if_no_key()
    logger.info(f"[LLM] Initialising {GEMINI_FLASH}")
    return GeminiChatModel(model=GEMINI_FLASH, api_key=settings.groq_api_key,
                            temperature=0.3, max_output_tokens=4096,
                            rate_limiter=_get_flash_rate_limiter(), max_retries=3)

@lru_cache(maxsize=1)
def get_gemini_pro() -> GeminiChatModel:
    _warn_if_no_key()
    logger.info(f"[LLM] Initialising {GEMINI_PRO} (pro mode)")
    return GeminiChatModel(model=GEMINI_PRO, api_key=settings.groq_api_key,
                            temperature=0.2, max_output_tokens=8192,
                            rate_limiter=_get_pro_rate_limiter(), max_retries=2)

@lru_cache(maxsize=1)
def get_gemini_flash_8b() -> GeminiChatModel:
    _warn_if_no_key()
    return GeminiChatModel(model=GEMINI_FLASH_8B, api_key=settings.groq_api_key,
                            temperature=0.1, max_output_tokens=2048,
                            rate_limiter=_get_flash_rate_limiter(), max_retries=3)

def get_gemini(model: str = DEFAULT_MODEL) -> GeminiChatModel:
    return {GEMINI_FLASH: get_gemini_flash, GEMINI_PRO: get_gemini_pro,
            GEMINI_FLASH_8B: get_gemini_flash_8b}.get(model, get_gemini_flash)()


async def check_gemini_connection() -> dict:
    if not settings.groq_api_key:
        return {"status": "not_configured"}
    try:
        r = await get_gemini_flash().ainvoke("Reply with the single word: OK")
        return {"status": "connected" if "ok" in r.content.lower() else "unexpected_response"}
    except Exception as e:
        logger.error(f"[LLM] Health check failed: {e}")
        return {"status": "error"}


def _warn_if_no_key() -> None:
    if not settings.groq_api_key:
        logger.warning("[LLM] GROQ_API_KEY not set — AI features will fail. Add it to .env")
