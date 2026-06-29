"""initial_schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-13 00:00:00.000000

Creates all Phase 1 tables:
  users, user_sessions, resumes, quiz_results,
  interview_sessions, career_scores, study_plans
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("email",            sa.String(255), nullable=False),
        sa.Column("hashed_password",  sa.String(255), nullable=False),
        sa.Column("name",             sa.String(100), nullable=False),
        sa.Column("target_role",      sa.String(100), nullable=True),
        sa.Column("current_skills",   postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active",        sa.Boolean(),   nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified",      sa.Boolean(),   nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── user_sessions ──────────────────────────────────────────────────────────
    op.create_table(
        "user_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_hash", sa.String(255), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_active",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])

    # ── resumes ────────────────────────────────────────────────────────────────
    op.create_table(
        "resumes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_name",        sa.String(255), nullable=False),
        sa.Column("file_path",        sa.String(500), nullable=False),
        sa.Column("raw_text",         sa.Text(),      nullable=True),
        sa.Column("ats_score",        sa.Integer(),   nullable=True),
        sa.Column("extracted_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("missing_skills",   postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suggestions",      postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("strengths",        postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("analyzed_at",      sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    # ── quiz_results ───────────────────────────────────────────────────────────
    op.create_table(
        "quiz_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("topic",        sa.String(100), nullable=False),
        sa.Column("difficulty",   sa.String(20),  nullable=False, server_default=sa.text("'medium'")),
        sa.Column("quiz_type",    sa.String(20),  nullable=True,  server_default=sa.text("'mcq'")),  # added
        sa.Column("questions",    postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score",        sa.Integer(),   nullable=True),
        sa.Column("weak_areas",   postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "taken_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_quiz_results_user_id", "quiz_results", ["user_id"])

    # ── interview_sessions ─────────────────────────────────────────────────────
    op.create_table(
        "interview_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_type",    sa.String(20),  nullable=False),
        sa.Column("target_role",     sa.String(100), nullable=True),
        sa.Column("questions",       postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("readiness_score", sa.Integer(),   nullable=True),
        sa.Column("feedback",        postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])

    # ── career_scores ──────────────────────────────────────────────────────────
    op.create_table(
        "career_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resume_score",    sa.Integer(), nullable=True),
        sa.Column("skill_score",     sa.Integer(), nullable=True),
        sa.Column("interview_score", sa.Integer(), nullable=True),
        sa.Column("quiz_score",      sa.Integer(), nullable=True),
        sa.Column("overall_score",   sa.Integer(), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_career_scores_user_id", "career_scores", ["user_id"])

    # ── study_plans ────────────────────────────────────────────────────────────
    op.create_table(
        "study_plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_type",   sa.String(20),  nullable=False),
        sa.Column("target_role", sa.String(100), nullable=True),
        sa.Column("plan_data",   postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active",   sa.Boolean(),   nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_study_plans_user_id", "study_plans", ["user_id"])


def downgrade() -> None:
    # Drop in reverse FK-dependency order
    op.drop_table("study_plans")
    op.drop_table("career_scores")
    op.drop_table("interview_sessions")
    op.drop_table("quiz_results")
    op.drop_table("resumes")
    op.drop_table("user_sessions")
    op.drop_table("users")
