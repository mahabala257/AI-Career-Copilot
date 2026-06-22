"""
app/rag/chromadb_client.py
───────────────────────────
ChromaDB client setup — the foundation of the entire RAG layer.

Why Gemini embeddings instead of sentence-transformers?
────────────────────────────────────────────────────────
The architecture doc listed sentence-transformers as the initial choice.
After testing this environment, we use GoogleGenerativeAIEmbeddings instead:

  1. sentence-transformers requires downloading ~90MB models from HuggingFace
     at startup. In production (Render free tier), this causes cold start
     timeouts and network restrictions.

  2. Gemini's text-embedding-004 model (768-dim) is:
     - Available via API key you already have
     - Consistently better at semantic search for technical content
     - Zero extra dependencies — same google-genai SDK already installed
     - Persistent across restarts (no re-download needed)

  3. In development without an API key, we fall back to a deterministic
     hash-based embedding function so the entire RAG layer can be tested
     without any external calls.

ChromaDB collections used
──────────────────────────
  interview_questions   — Q&A pairs for all roles and difficulty levels
  learning_resources    — courses, YouTube channels, docs, books
  company_info          — tech stacks, interview processes, culture
  career_guidance       — career advice, resume tips, job search strategies
  job_requirements      — skills required per role (used by Skill Gap Agent)

Storage
────────
  Local persistence at settings.chromadb_path (./chroma_store by default).
  On Render, mount a persistent disk at /data and set CHROMADB_PATH=/data/chroma.
  The store survives server restarts — no re-seeding needed.
"""

import hashlib
import logging
from functools import lru_cache
from typing import Optional

import chromadb
from chromadb import Collection

from app.config import settings

logger = logging.getLogger(__name__)

# ── Collection name constants ──────────────────────────────────────────────────
class CollectionName:
    INTERVIEW_QUESTIONS = "interview_questions"
    LEARNING_RESOURCES  = "learning_resources"
    COMPANY_INFO        = "company_info"
    CAREER_GUIDANCE     = "career_guidance"
    JOB_REQUIREMENTS    = "job_requirements"

    # Phase 2 collections
    LINKEDIN_TEMPLATES  = "linkedin_templates"
    PROJECT_TEMPLATES   = "project_templates"
    ENGLISH_TEMPLATES   = "english_templates"

    # Phase 3 collections
    COMPANY_INFORMATION    = "company_information"
    INTERNSHIP_INFORMATION = "internship_information"
    WELLNESS_RESOURCES     = "wellness_resources"

    ALL = [
        INTERVIEW_QUESTIONS,
        LEARNING_RESOURCES,
        COMPANY_INFO,
        CAREER_GUIDANCE,
        JOB_REQUIREMENTS,
        # Phase 2
        LINKEDIN_TEMPLATES,
        PROJECT_TEMPLATES,
        ENGLISH_TEMPLATES,
        # Phase 3
        COMPANY_INFORMATION,
        INTERNSHIP_INFORMATION,
        WELLNESS_RESOURCES,
    ]

# Embedding dimension for Gemini text-embedding-004
GEMINI_EMBEDDING_DIM = 768
# Fallback dimension when no API key (hash-based)
FALLBACK_EMBEDDING_DIM = 64


# ── Embedding function wrappers ────────────────────────────────────────────────

class GeminiEmbeddingFunction:
    """
    ChromaDB-compatible embedding function using Google Gemini.

    ChromaDB expects a callable that takes a list of strings and
    returns a list of float vectors. This class wraps LangChain's
    GoogleGenerativeAIEmbeddings to match that interface.

    Usage:
        ef = GeminiEmbeddingFunction()
        vectors = ef(["what is RAG?", "explain transformers"])
    """

    def __init__(self):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        self._model = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.google_api_key,
            # task_type="RETRIEVAL_DOCUMENT" for storage,
            # task_type="RETRIEVAL_QUERY" for querying
            # LangChain handles this automatically via embed_documents vs embed_query
        )
        logger.info("[ChromaDB] Using Gemini text-embedding-004 (768-dim)")

    def __call__(self, input: list[str]) -> list[list[float]]:
        """ChromaDB calls this with input= keyword argument."""
        return self._model.embed_documents(input)

    def name(self) -> str:
        return "gemini_embedding_function"

    def embed_query(self, text: str) -> list[float]:
        """Used for query-time embedding (different task_type internally)."""
        return self._model.embed_query(text)


class OpenAIEmbeddingFunction:
    """
    ChromaDB-compatible embedding function using OpenAI's embedding API.

    BUG-FIX: added as a fallback path for when GOOGLE_API_KEY is set but
    invalid — specifically, Google's newer "AQ." prefix API keys, which
    langchain-google-genai (and most third-party SDKs as of this writing)
    do not support, causing every embed call to fail with
    "API key not valid" even though the key works fine in AI Studio itself.

    text-embedding-3-small is 1536-dim, cheap (~$0.02 / 1M tokens), and has
    no free-tier account restrictions like the Gemini AQ. key issue.

    Usage:
        ef = OpenAIEmbeddingFunction()
        vectors = ef(["what is RAG?", "explain transformers"])
    """

    def __init__(self):
        from langchain_openai import OpenAIEmbeddings
        self._model = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        logger.info(
            f"[ChromaDB] Using OpenAI {settings.openai_embedding_model} "
            f"(fallback embedding provider)"
        )

    def __call__(self, input: list[str]) -> list[list[float]]:
        """ChromaDB calls this with input= keyword argument."""
        return self._model.embed_documents(input)

    def name(self) -> str:
        return "openai_embedding_function"

    def embed_query(self, text: str) -> list[float]:
        return self._model.embed_query(text)


class HashEmbeddingFunction:
    """
    Deterministic fallback embedding using SHA-256 hashing.

    Used when GOOGLE_API_KEY is not configured (dev/test mode).
    NOT suitable for production — hash similarity ≠ semantic similarity.
    But it lets the entire RAG pipeline run and be tested without API keys.

    The dim=64 produces 64-float vectors from the hash bytes.
    """

    def __init__(self, dim: int = FALLBACK_EMBEDDING_DIM):
        self.dim = dim
        logger.warning(
            "[ChromaDB] Using HASH embedding function (no GOOGLE_API_KEY). "
            "Semantic search will NOT work. Set GOOGLE_API_KEY for real RAG."
        )

    def name(self) -> str:
        return "hash_embedding_function"

    def __call__(self, input: list[str]) -> list[list[float]]:
        results = []
        for text in input:
            h = hashlib.sha256(text.encode()).digest()
            # Extend hash to fill dim by repeating
            extended = (h * ((self.dim // 32) + 1))[:self.dim]
            vector = [b / 255.0 for b in extended]
            results.append(vector)
        return results

    def embed_query(self, text: str) -> list[float]:
        return self.__call__([text])[0]


class FallbackEmbeddingFunction:
    """
    Wraps a primary embedding function and falls back to a secondary one
    if the primary fails AT CALL TIME (not just at construction time).

    BUG-FIX: this matters because GeminiEmbeddingFunction's constructor
    always succeeds (it just builds the LangChain client) — the actual
    "API key not valid" error only surfaces when .embed_documents() is
    called. A simple "if google_api_key: use Gemini else use X" check
    can't catch that; only a try/except around the real call can.
    """

    def __init__(self, primary, fallback):
        self._primary = primary
        self._fallback = fallback
        self._use_fallback = False  # sticky: once primary fails, stop retrying it

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not self._use_fallback:
            try:
                return self._primary(input)
            except Exception as e:
                logger.warning(
                    f"[ChromaDB] Primary embedding provider failed "
                    f"({type(e).__name__}: {e}). Switching to fallback "
                    f"provider for the rest of this session."
                )
                self._use_fallback = True
        return self._fallback(input)

    def name(self) -> str:
        return self._fallback.name() if self._use_fallback else self._primary.name()

    def embed_query(self, text: str) -> list[float]:
        if not self._use_fallback:
            try:
                return self._primary.embed_query(text)
            except Exception as e:
                logger.warning(
                    f"[ChromaDB] Primary embedding provider failed on query "
                    f"({type(e).__name__}: {e}). Switching to fallback."
                )
                self._use_fallback = True
        return self._fallback.embed_query(text)


def get_embedding_function():
    """
    Returns the appropriate embedding function based on configuration.

    Priority order:
      1. Gemini (if GOOGLE_API_KEY set) — falls back automatically to #2 or #3
         at call time if the key is rejected (e.g. "AQ." key format issue).
      2. OpenAI (if OPENAI_API_KEY set) — used as fallback for #1, or as
         primary if GOOGLE_API_KEY isn't set at all.
      3. Hash-based (always available) — last-resort fallback so the RAG
         pipeline never hard-crashes, even with zero API keys configured.
    """
    has_google = bool(settings.google_api_key)
    has_openai = bool(settings.openai_api_key)

    if has_google and has_openai:
        # Try Gemini first; auto-fall-back to OpenAI if Gemini calls fail
        return FallbackEmbeddingFunction(
            primary=GeminiEmbeddingFunction(),
            fallback=OpenAIEmbeddingFunction(),
        )
    if has_google:
        # No OpenAI configured — fall back to hash if Gemini fails
        return FallbackEmbeddingFunction(
            primary=GeminiEmbeddingFunction(),
            fallback=HashEmbeddingFunction(),
        )
    if has_openai:
        return OpenAIEmbeddingFunction()
    return HashEmbeddingFunction()


# ── ChromaDB client singleton ──────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    """
    Returns the singleton ChromaDB persistent client.

    PersistentClient stores all data to disk at settings.chromadb_path.
    The @lru_cache ensures we create exactly ONE client per process,
    avoiding file lock conflicts from multiple client instances.
    """
    import os
    os.makedirs(settings.chromadb_path, exist_ok=True)

    client = chromadb.PersistentClient(path=settings.chromadb_path)
    logger.info(f"[ChromaDB] Persistent client initialised at: {settings.chromadb_path}")
    return client


def get_or_create_collection(
    name: str,
    embedding_function=None,
    metadata: Optional[dict] = None,
) -> Collection:
    """
    Get an existing collection or create it if it doesn't exist.

    Uses cosine similarity (best for semantic text search).
    The embedding function is stored with the collection — all subsequent
    operations (add, query) use the same embedding function automatically.
    """
    client = get_chroma_client()
    ef     = embedding_function or get_embedding_function()

    col_metadata = {"hnsw:space": "cosine"}
    if metadata:
        col_metadata.update(metadata)

    collection = client.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata=col_metadata,
    )

    count = collection.count()
    logger.info(f"[ChromaDB] Collection '{name}': {count} documents")
    return collection


def get_collection(name: str, embedding_function=None) -> Optional[Collection]:
    """
    Get an existing collection. Returns None if it doesn't exist.
    Use this for read-only operations where you don't want to auto-create.
    """
    try:
        client = get_chroma_client()
        ef     = embedding_function or get_embedding_function()
        return client.get_collection(name=name, embedding_function=ef)
    except Exception:
        return None


def collection_exists(name: str) -> bool:
    """Check if a collection has been created and has documents."""
    col = get_collection(name)
    return col is not None and col.count() > 0


def get_collection_stats() -> dict[str, int]:
    """Return document count for every collection. Used by /health endpoint."""
    stats = {}
    for name in CollectionName.ALL:
        col = get_collection(name)
        stats[name] = col.count() if col else 0
    return stats