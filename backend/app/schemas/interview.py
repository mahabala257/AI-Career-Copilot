"""app/schemas/interview.py — Interview API schemas."""
from typing import Any, Optional
from pydantic import BaseModel, Field


class InterviewRequest(BaseModel):
    target_role:    str = Field(..., min_length=2, max_length=100)
    interview_type: str = Field(default="technical", pattern="^(hr|technical|coding)$")
    difficulty:     str = Field(default="medium",    pattern="^(easy|medium|hard)$")


class AnswerItem(BaseModel):
    question_id: int
    answer:      str = Field(..., min_length=1, max_length=5000)


class EvaluateRequest(BaseModel):
    session_id:  str
    target_role: str
    answers:     list[AnswerItem] = Field(..., min_length=1)


class QuestionItem(BaseModel):
    id:                         int
    question:                   str
    category:                   str = ""
    difficulty:                 str = "medium"
    expected_answer:            Optional[str]  = None
    key_concepts:               list[str]      = []
    follow_up_questions:        list[str]      = []
    estimated_answer_time_minutes: int         = 3
    # HR-specific
    what_interviewer_looks_for: Optional[str]  = None
    model_answer_structure:     Optional[str]  = None
    tips:                       list[str]      = []
    common_mistakes:            list[str]      = []
    # Coding-specific
    title:                      Optional[str]  = None
    examples:                   list[dict]     = []
    constraints:                list[str]      = []
    hints:                      list[str]      = []
    optimal_solution:           Optional[dict] = None
    companies_asked:            list[str]      = []


class InterviewResponse(BaseModel):
    session_id:                 str
    session_type:               str
    role:                       str
    difficulty:                 str
    questions:                  list[QuestionItem]
    total_questions:            int
    estimated_duration_minutes: int
    preparation_tips:           list[str] = []
    preparation_resources:      list[str] = []
    agent_error:                Optional[str] = None
    generated_at:               str


class EvaluationItem(BaseModel):
    question_id:           int
    score:                 int = Field(ge=0, le=10)
    grade:                 str
    strengths:             list[str] = []
    improvements:          list[str] = []
    model_points_covered:  list[str] = []
    model_points_missed:   list[str] = []
    feedback:              str = ""


class EvaluationResponse(BaseModel):
    overall_score:          int = Field(ge=0, le=100)
    overall_grade:          str
    evaluations:            list[EvaluationItem] = []
    readiness_assessment:   str = ""
    top_improvement_areas:  list[str] = []
    interview_tips:         list[str] = []
    evaluated_at:           str


class InterviewHistoryItem(BaseModel):
    session_id:      str
    session_type:    str
    target_role:     str
    readiness_score: Optional[int]
    created_at:      str
