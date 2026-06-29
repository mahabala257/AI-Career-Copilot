"""app/schemas/internship.py — Pydantic schemas for Internship Research API."""
from typing import Optional
from pydantic import BaseModel, Field


class InternshipResearchRequest(BaseModel):
    target_role:      str = Field(default="Software Engineer Intern", max_length=100)
    education_level:  str = Field(default="B.Tech 3rd year", max_length=50)
    college_tier:     str = Field(default="Tier 2", max_length=20)
    available_from:   str = Field(default="", max_length=30)
    duration_months:  Optional[int] = Field(default=None, ge=1, le=24)


class RecommendedInternship(BaseModel):
    company:                str = ""
    program_name:           str = ""
    company_type:           str = ""
    application_window:     str = ""
    stipend_range:           str = ""
    duration:                str = ""
    selection_process:      list[str] = []
    ppo_likelihood:          str = ""
    required_skills:        list[str] = []
    nice_to_have:           list[str] = []
    college_tier_accepted:  str = "all"
    application_platform:   str = ""
    fit_score:               int = 50


class ApplicationTimeline(BaseModel):
    three_months_before: str = Field(default="", alias="3_months_before")
    two_months_before:   str = Field(default="", alias="2_months_before")
    one_month_before:    str = Field(default="", alias="1_month_before")
    one_week_before:     str = Field(default="", alias="1_week_before")

    class Config:
        populate_by_name = True


class CoverLetterOutline(BaseModel):
    opening: str = ""
    body:    str = ""
    closing: str = ""


class PreparationPriority(BaseModel):
    priority: int = 1
    skill:    str = ""
    why:      str = ""
    resource: str = ""


class InternshipResearchResult(BaseModel):
    student_profile_summary:      str = ""
    recommended_companies:        list[RecommendedInternship] = []
    application_timeline:         dict = {}
    cover_letter_outline:         CoverLetterOutline = CoverLetterOutline()
    skill_gaps_for_internships:   list[str] = []
    preparation_priorities:       list[PreparationPriority] = []
    top_platforms:                list[str] = []
    resume_tips_for_internships:  list[str] = []
    networking_tips:              list[str] = []
    common_mistakes:              list[str] = []
    error_reason:                 Optional[str] = None


class InternshipResearchResponse(BaseModel):
    research_id:      str
    target_role:       str
    education_level:   str
    result:             InternshipResearchResult
    agent_error:        Optional[str] = None
    researched_at:      str


class InternshipHistoryItem(BaseModel):
    research_id:      str
    target_role:        Optional[str]
    education_level:    Optional[str]
    created_at:          str
