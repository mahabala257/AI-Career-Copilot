"""app/schemas/quiz.py — Quiz API schemas."""
from typing import Any, Optional
from pydantic import BaseModel, Field


class QuizRequest(BaseModel):
    topic:      str  = Field(default="",       max_length=100)
    difficulty: str  = Field(default="medium", pattern="^(easy|medium|hard)$")
    quiz_type:  str  = Field(default="mcq",    pattern="^(mcq|coding|mixed)$")


class QuizAnswerItem(BaseModel):
    question_id: int
    answer:      str = Field(..., min_length=1, max_length=2000)


class QuizSubmitRequest(BaseModel):
    quiz_id:  str
    answers:  list[QuizAnswerItem] = Field(..., min_length=1)


class QuizQuestionItem(BaseModel):
    id:           int
    question:     str
    options:      Optional[dict[str, str]] = None   # MCQ only
    topic_area:   str = ""
    difficulty:   str = "medium"
    # Coding only
    function_signature: Optional[str]  = None
    examples:           list[dict]     = []
    hints:              list[str]      = []
    time_limit_minutes: Optional[int]  = None


class QuizGenerateResponse(BaseModel):
    quiz_id:              str
    quiz_type:            str
    topic:                str
    difficulty:           str
    questions:            list[QuizQuestionItem]
    total_questions:      int
    topic_areas_covered:  list[str] = []
    agent_error:          Optional[str] = None
    generated_at:         str


class QuestionResult(BaseModel):
    question_id:    int
    user_answer:    str
    correct_answer: str
    is_correct:     bool
    topic_area:     str = ""


class QuizScoreResponse(BaseModel):
    quiz_id:                    str
    total_questions:            int
    correct_answers:            int
    score_percent:              int = Field(ge=0, le=100)
    grade:                      str
    question_results:           list[QuestionResult] = []
    weak_areas:                 list[str] = []
    strong_areas:               list[str] = []
    topic_performance:          dict[str, Any] = {}
    improvement_recommendations: list[str] = []
    next_quiz_focus:            list[str] = []
    encouragement:              str = ""
    scored_at:                  str
