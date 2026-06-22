"""app/schemas/linkedin.py — Pydantic schemas for LinkedIn Optimization API."""
from typing import Optional
from pydantic import BaseModel, Field


class LinkedInOptimizeRequest(BaseModel):
    headline:    str = Field(default="", max_length=220)
    about:       str = Field(default="", max_length=2600)
    experience:  str = Field(default="", max_length=5000)
    skills:      list[str] = Field(default_factory=list)
    target_role: str = Field(..., min_length=2, max_length=100)


class HeadlineSection(BaseModel):
    current:   str = ""
    optimized: str = ""
    reasoning: str = ""


class AboutSection(BaseModel):
    current_summary: str = ""
    optimized:       str = ""
    hook_score:      int = 0
    reasoning:       str = ""


class ExperienceBullet(BaseModel):
    original:    str = ""
    rewritten:   str = ""
    improvement: str = ""


class SkillsReorder(BaseModel):
    recommended_top_3: list[str] = []
    skills_to_add:     list[str] = []
    skills_to_remove:  list[str] = []
    reasoning:         str = ""


class LinkedInSections(BaseModel):
    headline:           HeadlineSection = HeadlineSection()
    about:              AboutSection = AboutSection()
    experience_bullets: list[ExperienceBullet] = []
    skills_reorder:     SkillsReorder = SkillsReorder()


class KeywordDensity(BaseModel):
    present_keywords:            list[str] = []
    missing_high_value_keywords: list[str] = []
    keyword_score:               int = 0


class LinkedInOptimizationResult(BaseModel):
    current_score:              int = 0
    optimized_score:            int = 0
    score_breakdown:            dict = {}
    sections:                   LinkedInSections = LinkedInSections()
    keyword_density:            KeywordDensity = KeywordDensity()
    top_3_changes:              list[str] = []
    creator_tips:               list[str] = []
    profile_completeness_tips:  list[str] = []
    error_reason:               Optional[str] = None


class LinkedInOptimizeResponse(BaseModel):
    optimization_id: str
    target_role:     str
    result:          LinkedInOptimizationResult
    agent_error:     Optional[str] = None
    optimized_at:    str


class LinkedInHistoryItem(BaseModel):
    optimization_id:  str
    target_role:      Optional[str]
    current_score:    Optional[int]
    optimized_score:  Optional[int]
    created_at:       str
