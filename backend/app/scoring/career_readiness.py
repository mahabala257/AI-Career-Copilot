"""
app/scoring/career_readiness.py
─────────────────────────────────
Career Readiness Score Engine.

Aggregates outputs from all agents into a single 0-100 score
with weighted components and prioritised recommendations.

Weights (Phase 1):
  resume_score    × 0.30  — ATS compatibility
  skill_score     × 0.25  — readiness% from Skill Gap Agent
  quiz_score      × 0.25  — average quiz performance
  interview_score × 0.20  — interview session readiness
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


WEIGHTS = {
    "resume_score":    0.30,
    "skill_score":     0.25,
    "quiz_score":      0.25,
    "interview_score": 0.20,
}

GRADE_THRESHOLDS = [
    (90, "Excellent",       "You are highly job-ready. Focus on niche skills and portfolio polish."),
    (75, "Good",            "Strong foundation. Close 2-3 skill gaps to significantly boost employability."),
    (60, "Developing",      "On the right track. Consistent daily practice will move you into the Good tier within 4-6 weeks."),
    (45, "Early Stage",     "Good starting point. Focus on building one strong project and closing critical skill gaps."),
    (0,  "Getting Started", "Everyone starts here. Follow the study plan and your score will improve weekly."),
]


@dataclass
class CareerReadinessScore:
    resume_score:    int = 0
    skill_score:     int = 0
    quiz_score:      int = 0
    interview_score: int = 0
    overall_score:   int = 0
    grade:           str = "Getting Started"
    message:         str = ""
    recommendations: list[str] = field(default_factory=list)
    next_milestone:  str = ""


def compute_career_readiness(
    resume_score:    Optional[int] = None,
    skill_score:     Optional[int] = None,
    quiz_score:      Optional[int] = None,
    interview_score: Optional[int] = None,
) -> CareerReadinessScore:
    """
    Compute the Career Readiness Score from component scores.
    None values are treated as 0 and excluded from weight normalisation.
    """
    components = {
        "resume_score":    resume_score    or 0,
        "skill_score":     skill_score     or 0,
        "quiz_score":      quiz_score      or 0,
        "interview_score": interview_score or 0,
    }

    # Only include components that have been computed (non-zero)
    active = {k: v for k, v in components.items() if (
        (k == "resume_score"    and resume_score    is not None) or
        (k == "skill_score"     and skill_score     is not None) or
        (k == "quiz_score"      and quiz_score      is not None) or
        (k == "interview_score" and interview_score is not None)
    )}

    if not active:
        return CareerReadinessScore(
            recommendations=["Complete your profile and upload your resume to get started."]
        )

    # Normalise weights to only active components
    total_weight = sum(WEIGHTS[k] for k in active)
    overall = int(sum(v * WEIGHTS[k] / total_weight for k, v in active.items()))
    overall = max(0, min(100, overall))

    grade, message = _get_grade(overall)
    recommendations = _build_recommendations(components, overall)
    next_milestone   = _next_milestone(overall)

    return CareerReadinessScore(
        resume_score=components["resume_score"],
        skill_score=components["skill_score"],
        quiz_score=components["quiz_score"],
        interview_score=components["interview_score"],
        overall_score=overall,
        grade=grade,
        message=message,
        recommendations=recommendations,
        next_milestone=next_milestone,
    )


def _get_grade(score: int) -> tuple[str, str]:
    for threshold, grade, message in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade, message
    return "Getting Started", ""


def _build_recommendations(components: dict, overall: int) -> list[str]:
    recs = []
    if components["resume_score"] < 70:
        recs.append("Upload an updated resume — your ATS score has the most impact on callbacks.")
    if components["skill_score"] < 60:
        recs.append("Run a Skill Gap Analysis to identify your highest-priority skills to learn.")
    if components["quiz_score"] < 65:
        recs.append("Practice daily quizzes — even 10 minutes per day compounds fast.")
    if components["interview_score"] < 60:
        recs.append("Complete a mock Technical Interview to build confidence and identify weak topics.")
    if not recs:
        recs.append("You're performing well across all dimensions. Keep the momentum going!")
    return recs[:3]


def _next_milestone(score: int) -> str:
    milestones = [
        (90, "Reach 90+ — Top candidate territory"),
        (75, "Reach 75 — Strong candidate status"),
        (60, "Reach 60 — Developing to Good tier"),
        (45, "Reach 45 — Early Stage to Developing tier"),
        (0,  "Reach 30 — Complete your first assessment"),
    ]
    for threshold, label in milestones:
        if score < threshold:
            return label
    return "Maintain excellence — keep skills current"
