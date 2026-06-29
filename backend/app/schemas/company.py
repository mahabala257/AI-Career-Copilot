"""app/schemas/company.py — Pydantic schemas for Company Research API."""
from typing import Optional
from pydantic import BaseModel, Field


class CompanyResearchRequest(BaseModel):
    company_name:    str = Field(..., min_length=2, max_length=100)
    target_role:     str = Field(default="Software Engineer", max_length=100)
    work_mode:       Optional[str] = None   # "Remote" | "Hybrid" | "Onsite" | "Any"
    employment_type: Optional[str] = None   # "Full-time" | "Part-time" | "Contract" | "Internship" | "Any"


class InterviewRound(BaseModel):
    round: str = ""
    focus: str = ""
    tips:  str = ""


class KnownQuestion(BaseModel):
    type:    str = ""
    example: str = ""


class SkillAlignment(BaseModel):
    matching_skills:  list[str] = []
    missing_skills:   list[str] = []
    alignment_score:  int = 0


class PrepStrategyWeek(BaseModel):
    week:        int = 1
    focus:       str = ""
    daily_hours: float = 1.0
    resources:   list[str] = []


class TypicalOpening(BaseModel):
    role:            str = ""
    work_mode:       str = ""
    employment_type: str = ""
    salary_range:    str = ""
    required_skills: list[str] = []


class CompanyResearchResult(BaseModel):
    company_name:          str = ""
    company_type:          str = ""
    overview:               str = ""
    tech_stack:             list[str] = []
    engineering_culture:    str = ""
    interview_style:        str = ""
    interview_rounds:       list[InterviewRound] = []
    culture_values:         list[str] = []
    known_question_types:   list[KnownQuestion] = []
    skill_alignment:        SkillAlignment = SkillAlignment()
    prep_strategy:          list[PrepStrategyWeek] = []
    typical_timeline:       str = ""
    salary_range:           str = ""
    pros:                   list[str] = []
    cons:                   list[str] = []
    glassdoor_rating:        Optional[float] = None
    application_tips:       list[str] = []
    typical_openings:       list[TypicalOpening] = []
    error_reason:           Optional[str] = None


class CompanyResearchResponse(BaseModel):
    research_id:  str
    company_name: str
    target_role:  str
    result:       CompanyResearchResult
    agent_error:  Optional[str] = None
    researched_at: str


class CompanyHistoryItem(BaseModel):
    research_id:     str
    company_name:    Optional[str]
    target_role:     Optional[str]
    alignment_score: Optional[int]
    created_at:      str
