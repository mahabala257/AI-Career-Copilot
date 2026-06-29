"""phase2_linkedin_projects_english

Revision ID: 0002_phase2_tables
Revises: 0001_initial_schema
Create Date: 2026-06-14 00:00:00.000000

Creates three Phase 2 tables:
  linkedin_optimizations    — LinkedIn Optimization Agent
  project_recommendations   — Project Recommendation Agent
  english_evaluations       — Spoken English Agent
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_phase2_tables"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── linkedin_optimizations ─────────────────────────────────────────────────
    op.create_table(
        "linkedin_optimizations",
        sa.Column("id",                 postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id",            postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_headline",  sa.Text,        nullable=True),
        sa.Column("original_about",     sa.Text,        nullable=True),
        sa.Column("original_experience",sa.Text,        nullable=True),
        sa.Column("original_skills",    postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("current_score",      sa.Integer(),   nullable=True),
        sa.Column("optimized_score",    sa.Integer(),   nullable=True),
        sa.Column("optimization_data",  postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("target_role",        sa.String(100), nullable=True),
        sa.Column("created_at",         sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_linkedin_optimizations_user_id", "linkedin_optimizations", ["user_id"])

    # ── project_recommendations ────────────────────────────────────────────────
    op.create_table(
        "project_recommendations",
        sa.Column("id",                   postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id",              postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_role",          sa.String(100), nullable=True),
        sa.Column("experience_level",     sa.String(20),  nullable=True),
        sa.Column("time_available_weeks", sa.Integer(),   nullable=True),
        sa.Column("recommendations_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("portfolio_score",      sa.Integer(),   nullable=True),
        sa.Column("created_at",           sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_recommendations_user_id", "project_recommendations", ["user_id"])

    # ── english_evaluations ────────────────────────────────────────────────────
    op.create_table(
        "english_evaluations",
        sa.Column("id",                  postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id",             postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_text",       sa.Text, nullable=False),
        sa.Column("corrected_text",      sa.Text, nullable=True),
        sa.Column("context_type",        sa.String(30),  nullable=True),
        sa.Column("question_answered",   sa.Text,        nullable=True),
        sa.Column("overall_score",       sa.Integer(),   nullable=True),
        sa.Column("scores_breakdown",    postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("issues",              postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("star_compliance",     postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("practice_scripts",   postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("vocabulary_upgrades", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at",          sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_english_evaluations_user_id", "english_evaluations", ["user_id"])


def downgrade() -> None:
    op.drop_table("english_evaluations")
    op.drop_table("project_recommendations")
    op.drop_table("linkedin_optimizations")
