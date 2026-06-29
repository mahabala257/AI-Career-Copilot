"""app/schemas/project.py — Pydantic schemas for Project Recommendation API."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ProjectRecommendRequest(BaseModel):
    target_role:          str = Field(..., min_length=2, max_length=100)
    experience_level:     Literal["fresher", "1-2 years", "2-3 years", "3-5 years", "5+ years"] = "fresher"
    time_available_weeks: int = Field(default=4, ge=1, le=52)


class TechStack(BaseModel):
    backend:  list[str] = []
    frontend: list[str] = []
    ai_ml:    list[str] = []
    database: list[str] = []
    devops:   list[str] = []


class RecommendedProject(BaseModel):
    rank:                      int
    title:                     str
    one_liner:                 str = ""
    description:               str = ""
    why_this_impresses:        str = ""
    skills_demonstrated:       list[str] = []
    skills_learned:            list[str] = []
    estimated_weeks:           int = 2
    difficulty:                str = "intermediate"
    tech_stack:                TechStack = TechStack()
    github_readme_sections:    list[str] = []
    interview_talking_points:  list[str] = []
    scale_question:            str = ""
    demo_tip:                  str = ""


class ProjectToAvoid(BaseModel):
    project: str
    reason:  str = ""


class ProjectRecommendationResult(BaseModel):
    portfolio_score:       int = 0
    portfolio_assessment:  str = ""
    recommended_projects:  list[RecommendedProject] = []
    projects_to_avoid:     list[ProjectToAvoid] = []
    portfolio_target_score: int = 75
    portfolio_action_plan: list[str] = []
    error_reason:          Optional[str] = None


class ProjectRecommendResponse(BaseModel):
    recommendation_id:    str
    target_role:          str
    experience_level:     str
    result:               ProjectRecommendationResult
    agent_error:          Optional[str] = None
    generated_at:         str


class ProjectHistoryItem(BaseModel):
    recommendation_id:  str
    target_role:        Optional[str]
    experience_level:   Optional[str]
    portfolio_score:    Optional[int]
    created_at:         str
