"""
app/db/migrations/env.py
─────────────────────────
Alembic migration environment — configured for our async SQLAlchemy setup.

Key customizations from the default Alembic template:
  1. Imports all ORM models so autogenerate can detect schema changes
  2. Reads DATABASE_URL from our Settings class (not alembic.ini)
  3. Uses sync psycopg2 driver for Alembic (Alembic doesn't support asyncpg)
  4. Sets compare_type=True so column type changes are auto-detected

How to use:
  # Create a new migration after changing models:
  alembic revision --autogenerate -m "add linkedin_score to career_scores"

  # Apply all pending migrations:
  alembic upgrade head

  # Rollback one migration:
  alembic downgrade -1
"""

import sys
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Make app importable from migrations directory ──────────────────────────────
# Alembic runs from the backend/ directory, so we add it to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.config import settings
from app.db.database import Base

# Import ALL models here so Alembic's autogenerate sees them.
# If you add a new model and don't import it here, autogenerate will
# try to DROP the table thinking it's stale.
from app.models.user import User
from app.models.models import (
    UserSession,
    Resume,
    QuizResult,
    InterviewSession,
    CareerScore,
    StudyPlan,
)

# Alembic config object
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Our models' metadata — used for autogenerate
target_metadata = Base.metadata

# Override the sqlalchemy.url in alembic.ini with our settings value.
# This way there's ONE source of truth for the database URL (settings.py).
# Alembic needs the SYNC psycopg2 URL (not asyncpg).
config.set_main_option("sqlalchemy.url", settings.sync_database_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generates SQL script without DB connection).
    Useful for reviewing migrations before applying them.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,        # Detect column type changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (applies directly to the database).
    This is what `alembic upgrade head` uses.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,    # NullPool: don't reuse connections in migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
