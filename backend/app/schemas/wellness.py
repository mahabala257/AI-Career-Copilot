"""app/schemas/wellness.py — Pydantic schemas for Wellness & Motivation API."""
from typing import Optional
from pydantic import BaseModel, Field


class WellnessCheckinRequest(BaseModel):
    mood_message: str = Field(..., min_length=3, max_length=2000)


class BurnoutRisk(BaseModel):
    level:          str = "low"   # low | medium | high
    signals:        list[str] = []
    recommendation: str = ""


class AdjustedStudyPlan(BaseModel):
    recommendation: str = ""
    reason:         str = ""


class CrisisResources(BaseModel):
    india:   dict = {}
    message: str = ""


class WellnessResult(BaseModel):
    emotional_validation:      str = ""
    reframe:                   str = ""
    next_single_action:        str = ""
    progress_acknowledgment:   str = ""
    burnout_risk:              BurnoutRisk = BurnoutRisk()
    motivational_quote:        str = ""
    weekly_reflection_prompt:  str = ""
    adjusted_study_plan:       AdjustedStudyPlan = AdjustedStudyPlan()
    career_perspective:        str = ""
    professional_help_note:    Optional[str] = None
    professional_help_flag:    bool = False
    crisis_resources:          Optional[CrisisResources] = None
    error_reason:              Optional[str] = None


class WellnessCheckinResponse(BaseModel):
    checkin_id:   str
    result:        WellnessResult
    agent_error:   Optional[str] = None
    checked_in_at: str


class WellnessHistoryItem(BaseModel):
    checkin_id:          str
    burnout_risk_level:  Optional[str]
    created_at:           str
