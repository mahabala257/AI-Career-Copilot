"""
config.py
─────────
Central configuration using pydantic-settings.
All environment variables are loaded here, type-validated, and exposed
as a single `settings` singleton imported everywhere else.

Why pydantic-settings instead of os.getenv()?
  - Type coercion: PORT="8000" becomes int automatically
  - Validation: missing required keys fail at startup, not at runtime
  - IDE autocomplete on settings.DATABASE_URL vs a dict key
  - .env file loading built-in
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── pydantic-settings config ──────────────────────────────────────────────
    # Tells pydantic-settings to read from a .env file automatically.
    # extra="ignore" means unknown env vars don't raise errors (useful when
    # running inside Docker/Render where the host injects extra variables).
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "AI Career Copilot"
    app_version: str = "1.0.0"
    environment: str = "development"
    # Default False — must be explicitly set to True in local .env for debug output.
    # This prevents SQL statement logging (which can include PII) in production.
    debug: bool = False

    # ── API Server ─────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── CORS ───────────────────────────────────────────────────────────────────
    # Stored as a comma-separated string in .env, parsed into a list here.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # ── PostgreSQL ─────────────────────────────────────────────────────────────
    # SQLAlchemy async URL uses asyncpg driver.
    # In production (Render), DATABASE_URL is injected automatically.
    database_url: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/career_copilot"
    )

    # Sync URL for Alembic (Alembic runs migrations synchronously)
    @property
    def sync_database_url(self) -> str:
        # Replace asyncpg driver with psycopg2 for Alembic
        return self.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        )

    # ── JWT ────────────────────────────────────────────────────────────────────
    jwt_secret_key: str = "CHANGE-THIS-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # FIX-11: Reject known-insecure placeholder values at startup.
    # Generate a safe key with: openssl rand -hex 32
    @field_validator("jwt_secret_key")
    @classmethod
    def jwt_key_must_be_secure(cls, v: str) -> str:
        insecure = {
            "CHANGE-THIS-IN-PRODUCTION",
            "change-this-in-production",
            "change-this-to-a-secure-random-string-in-production",
            "",
        }
        if v in insecure:
            raise ValueError(
                "JWT_SECRET_KEY is set to an insecure placeholder. "
                "Generate a secure key with: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters. "
                "Generate a secure key with: openssl rand -hex 32"
            )
        return v

    # ── LLMs ──────────────────────────────────────────────────────────────────
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    groq_api_key: str = ""
    groq_model: str = "llama3-70b-8192"

    # BUG-FIX: fallback embedding provider for when Gemini API keys are
    # unavailable/invalid (e.g. Google's "AQ." key rollout, which many
    # third-party SDKs including langchain-google-genai don't yet support).
    # Optional — only used by get_embedding_function() if set.
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # ── LangFuse ───────────────────────────────────────────────────────────────
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # ── ChromaDB ───────────────────────────────────────────────────────────────
    chromadb_path: str = "./chroma_store"
    chromadb_collection_name: str = "career_copilot_knowledge"

    # ── File Uploads ───────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    # ── Computed helpers ───────────────────────────────────────────────────────
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# ── Singleton ──────────────────────────────────────────────────────────────────
# @lru_cache ensures this is only created once no matter how many times
# get_settings() is called across the codebase.
# FastAPI's Depends(get_settings) pattern works perfectly with this.
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Module-level singleton for direct imports:
# from app.config import settings
settings = get_settings()