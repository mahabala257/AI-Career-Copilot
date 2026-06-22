"""
app/schemas/resume.py
──────────────────────
Pydantic schemas for resume API endpoints.

These define the exact JSON shape the frontend receives.
They are completely separate from ORM models — the service layer
maps between the two.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ── Sub-schemas ────────────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    skills_match:          int = Field(ge=0, le=100)
    experience_relevance:  int = Field(ge=0, le=100)
    education_fit:         int = Field(ge=0, le=100)
    keyword_optimization:  int = Field(ge=0, le=100)
    formatting_clarity:    int = Field(ge=0, le=100)


class ResumeAnalysis(BaseModel):
    ats_score:             int                    = Field(ge=0, le=100)
    extracted_skills:      list[str]              = []
    missing_skills:        list[str]              = []
    top_matching_skills:   list[str]              = []
    critical_missing:      list[str]              = []
    strengths:             list[str]              = []
    suggestions:           list[str]              = []
    experience_level:      str                    = "unknown"
    improvement_priority:  str                    = "skills"
    score_breakdown:       Optional[ScoreBreakdown] = None
    education_match:       int                    = Field(default=0, ge=0, le=100)
    keyword_density_score: int                    = Field(default=0, ge=0, le=100)
    format_score:          int                    = Field(default=0, ge=0, le=100)
    target_role:           str                    = ""
    error_reason:          Optional[str]          = None


# ── Response schemas ───────────────────────────────────────────────────────────

class ResumeAnalysisResponse(BaseModel):
    """Returned by POST /api/resume/analyze"""
    resume_id:       str
    filename:        str
    page_count:      int
    word_count:      int
    sections:        list[str]
    analysis:        ResumeAnalysis
    parse_warnings:  list[str]             = []
    agent_error:     Optional[str]         = None
    analyzed_at:     str


class ResumeHistoryItem(BaseModel):
    """Single item in GET /api/resume/history list"""
    resume_id:    str
    filename:     str
    ats_score:    Optional[int]
    analyzed_at:  Optional[str]
    created_at:   str
    skills_count: int
    missing_count: int


class ResumeHistoryResponse(BaseModel):
    items:  list[ResumeHistoryItem]
    total:  int


class ResumeDetailResponse(BaseModel):
    """Returned by GET /api/resume/{id}"""
    resume_id:        str
    filename:         str
    ats_score:        Optional[int]
    extracted_skills: list[str]
    missing_skills:   list[str]
    suggestions:      list[str]
    strengths:        list[str]
    analyzed_at:      Optional[str]
    created_at:       str
    raw_text_preview: str
