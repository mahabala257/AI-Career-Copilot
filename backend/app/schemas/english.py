"""app/schemas/english.py — Pydantic schemas for Spoken English API."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class EnglishEvaluateRequest(BaseModel):
    spoken_text:   str = Field(..., min_length=20, max_length=5000,
                               description="The text/transcript to evaluate")
    context_type:  Literal["interview_answer", "self_intro", "email", "presentation"] = "interview_answer"
    question:      str = Field(default="", max_length=300,
                               description="The question being answered (for structure evaluation)")


class ScriptGenerateRequest(BaseModel):
    experience_level: str = Field(default="fresher", max_length=20)


class EnglishScores(BaseModel):
    grammar:     int = Field(ge=0, le=100, default=0)
    fluency:     int = Field(ge=0, le=100, default=0)
    structure:   int = Field(ge=0, le=100, default=0)
    vocabulary:  int = Field(ge=0, le=100, default=0)
    conciseness: int = Field(ge=0, le=100, default=0)
    overall:     int = Field(ge=0, le=100, default=0)


class EnglishIssue(BaseModel):
    type:        str = ""   # filler_word | grammar | vocabulary | structure | clarity
    found:       str = ""
    suggestion:  str = ""
    explanation: str = ""


class Annotation(BaseModel):
    original:  str = ""
    corrected: str = ""
    reason:    str = ""


class StarCompliance(BaseModel):
    situation: bool = False
    task:      bool = False
    action:    bool = False
    result:    bool = False
    score:     int = 0
    missing:   str = ""
    tip:       str = ""


class VocabularyUpgrade(BaseModel):
    weak:    str = ""
    strong:  str = ""
    context: str = ""


class PracticeScripts(BaseModel):
    elevator_pitch_30s: str = ""
    self_intro_2min:    str = ""
    hr_answers:         dict = {}


class EnglishEvaluationResult(BaseModel):
    original_text:       str = ""
    corrected_text:      str = ""
    scores:              EnglishScores = EnglishScores()
    issues:              list[EnglishIssue] = []
    annotations:         list[Annotation] = []
    star_compliance:     StarCompliance = StarCompliance()
    vocabulary_upgrades: list[VocabularyUpgrade] = []
    practice_scripts:    PracticeScripts = PracticeScripts()
    top_3_improvements:  list[str] = []
    encouragement:       str = ""
    error_reason:        Optional[str] = None


class EnglishEvaluateResponse(BaseModel):
    evaluation_id: str
    context_type:  str
    result:        EnglishEvaluationResult
    agent_error:   Optional[str] = None
    evaluated_at:  str


class ScriptGenerateResponse(BaseModel):
    scripts:      PracticeScripts
    generated_at: str


class EnglishHistoryItem(BaseModel):
    evaluation_id:  str
    context_type:   Optional[str]
    overall_score:  Optional[int]
    created_at:     str
