"""
app/schemas/skill_gap.py
─────────────────────────
Pydantic schemas for skill gap API endpoints.
"""
from typing import Optional
from pydantic import BaseModel, Field


class MatchedSkill(BaseModel):
    skill:           str
    candidate_level: str = "basic"
    required_level:  str = "intermediate"
    gap:             str = "none"


class MissingSkill(BaseModel):
    skill:              str
    category:           str = "general"
    priority:           str = "medium"   # critical | high | medium | low
    why_important:      str = ""
    time_to_learn:      str = "2-4 weeks"
    learning_resources: list[str] = []


class SkillCategories(BaseModel):
    strong:               list[str] = []
    developing:           list[str] = []
    missing_critical:     list[str] = []
    missing_nice_to_have: list[str] = []


class SkillGapAnalysis(BaseModel):
    target_role:               str
    overall_readiness_percent: int = Field(ge=0, le=100)
    current_skills:            list[str] = []
    required_skills:           list[str] = []
    matched_skills:            list[MatchedSkill] = []
    missing_skills:            list[MissingSkill] = []
    priority_order:            list[str] = []
    skill_categories:          SkillCategories = SkillCategories()
    months_to_job_ready:       int = 6
    immediate_actions:         list[str] = []
    strengths_to_highlight:    list[str] = []
    error_reason:              Optional[str] = None


# ── Request ────────────────────────────────────────────────────────────────────
class SkillGapRequest(BaseModel):
    target_role:            str = Field(..., min_length=2, max_length=100)
    current_skills:         list[str] = []
    generate_learning_path: bool = False
    generate_roadmap:       bool = False
    available_hours:        float = Field(default=2.0, ge=0.5, le=12.0)


# ── Response ───────────────────────────────────────────────────────────────────
class SkillGapResponse(BaseModel):
    analysis:       SkillGapAnalysis
    agent_error:    Optional[str] = None
    analyzed_at:    str


class LearningPathItem(BaseModel):
    skill:             str
    why_critical:      str = ""
    estimated_weeks:   int = 2
    phases:            list[dict] = []
    project_idea:      str = ""
    interview_questions: list[str] = []


class LearningPathResponse(BaseModel):
    target_role:           str
    learning_paths:        list[LearningPathItem] = []
    suggested_sequence:    list[str] = []
    total_estimated_weeks: int = 0
