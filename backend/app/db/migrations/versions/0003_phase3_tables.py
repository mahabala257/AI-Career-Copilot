"""phase3_company_internship_wellness

Revision ID: 0003_phase3_tables
Revises: 0002_phase2_tables
Create Date: 2026-06-15 00:00:00.000000

Creates three Phase 3 tables:
  company_researches      — Company Research Agent
  internship_researches   — Internship Research Agent
  wellness_checkins       — Wellness & Motivation Agent
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_phase3_tables"
down_revision = "0002_phase2_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── company_researches ─────────────────────────────────────────────────────
    op.create_table(
        "company_researches",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id",         postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_name",    sa.String(100), nullable=False),
        sa.Column("target_role",     sa.String(100), nullable=True),
        sa.Column("alignment_score", sa.Integer(),   nullable=True),
        sa.Column("research_data",   postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_company_researches_user_id", "company_researches", ["user_id"])
    op.create_index("ix_company_researches_company", "company_researches", ["company_name"])

    # ── internship_researches ──────────────────────────────────────────────────
    op.create_table(
        "internship_researches",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id",         postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_role",     sa.String(100), nullable=True),
        sa.Column("education_level", sa.String(50),  nullable=True),
        sa.Column("college_tier",    sa.String(20),  nullable=True),
        sa.Column("available_from",  sa.String(30),  nullable=True),
        sa.Column("research_data",   postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_internship_researches_user_id", "internship_researches", ["user_id"])

    # ── wellness_checkins ──────────────────────────────────────────────────────
    op.create_table(
        "wellness_checkins",
        sa.Column("id",                     postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id",                postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mood_message",           sa.Text,        nullable=True),
        sa.Column("burnout_risk_level",     sa.String(10),  nullable=True),
        sa.Column("response_data",          postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("professional_help_flag", sa.Boolean(),   nullable=False, server_default=sa.text("false")),
        sa.Column("created_at",             sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_wellness_checkins_user_id", "wellness_checkins", ["user_id"])


def downgrade() -> None:
    op.drop_table("wellness_checkins")
    op.drop_table("internship_researches")
    op.drop_table("company_researches")
