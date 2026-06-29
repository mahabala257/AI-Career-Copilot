"""
app/services/report_service.py
───────────────────────────────
Generates a polished, downloadable PDF "Career Readiness Report" for a user,
pulling together their latest resume analysis, skill gaps, quiz/interview
history, study plan, and overall career score. Uses PyMuPDF (already a
dependency for resume parsing) — no extra packages required.
"""
import logging
import uuid
from datetime import datetime, timezone

import fitz  # PyMuPDF
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CareerScore, InterviewSession, QuizResult, Resume, StudyPlan
from app.models.user import User
from app.scoring.career_readiness import compute_career_readiness

logger = logging.getLogger(__name__)

# ── Layout constants ────────────────────────────────────────────────────────
PAGE_W, PAGE_H = 595, 842          # A4 in points
MARGIN = 50
CONTENT_W = PAGE_W - 2 * MARGIN
PRIMARY = (0.40, 0.22, 0.92)       # purple
DARK = (0.12, 0.13, 0.18)
GREY = (0.45, 0.47, 0.52)
GREEN = (0.18, 0.49, 0.20)
LIGHTBG = (0.96, 0.96, 0.99)


class _Pdf:
    """Tiny flowing-layout helper over PyMuPDF (tracks Y, handles page breaks)."""

    def __init__(self):
        self.doc = fitz.open()
        self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        self.y = MARGIN

    def _space(self, h: float):
        if self.y + h > PAGE_H - MARGIN:
            self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
            self.y = MARGIN

    def text(self, s: str, size=11, color=DARK, bold=False, gap=4, indent=0):
        s = s or ""
        font = "helv" if not bold else "hebo"
        rect = fitz.Rect(MARGIN + indent, self.y, PAGE_W - MARGIN, PAGE_H - MARGIN)
        # measure required height by laying out into a tall box first
        needed = self._height(s, size, font, CONTENT_W - indent)
        self._space(needed + gap)
        rect = fitz.Rect(MARGIN + indent, self.y, PAGE_W - MARGIN, self.y + needed + 2)
        self.page.insert_textbox(rect, s, fontsize=size, fontname=font, color=color, align=0)
        self.y += needed + gap

    def _height(self, s: str, size: float, font: str, width: float) -> float:
        # Rough wrap estimate: PyMuPDF char width ~0.5*size for helv
        import math
        line_h = size * 1.35
        approx_chars = max(1, int(width / (size * 0.50)))
        lines = 0
        for para in s.split("\n"):
            lines += max(1, math.ceil(len(para) / approx_chars))
        return lines * line_h + 2

    def heading(self, s: str):
        self._space(28)
        self.y += 6
        self.text(s, size=14, color=PRIMARY, bold=True, gap=2)
        # underline rule
        self.page.draw_line(fitz.Point(MARGIN, self.y), fitz.Point(PAGE_W - MARGIN, self.y),
                            color=PRIMARY, width=0.8)
        self.y += 8

    def bullet(self, s: str):
        self.text(f"•  {s}", size=10.5, indent=8, gap=3)

    def kv_row(self, label: str, value: str):
        self.text(f"{label}:  {value}", size=11, gap=3)

    def banner(self, title: str, subtitle: str):
        self.page.draw_rect(fitz.Rect(0, 0, PAGE_W, 90), color=PRIMARY, fill=PRIMARY)
        self.page.insert_textbox(fitz.Rect(MARGIN, 26, PAGE_W - MARGIN, 54),
                                 title, fontsize=20, fontname="hebo", color=(1, 1, 1))
        self.page.insert_textbox(fitz.Rect(MARGIN, 56, PAGE_W - MARGIN, 80),
                                 subtitle, fontsize=10.5, fontname="helv", color=(0.9, 0.9, 1))
        self.y = 110

    def score_box(self, score: int, grade: str):
        self._space(70)
        r = fitz.Rect(MARGIN, self.y, MARGIN + 150, self.y + 60)
        self.page.draw_rect(r, color=PRIMARY, fill=LIGHTBG, width=1)
        self.page.insert_textbox(fitz.Rect(MARGIN, self.y + 8, MARGIN + 150, self.y + 40),
                                 f"{score}/100", fontsize=24, fontname="hebo", color=PRIMARY, align=1)
        self.page.insert_textbox(fitz.Rect(MARGIN, self.y + 40, MARGIN + 150, self.y + 56),
                                 grade, fontsize=11, fontname="helv", color=GREY, align=1)
        self.y += 70

    def bytes(self) -> bytes:
        return self.doc.tobytes()


async def generate_career_report_pdf(user_id: str, db: AsyncSession) -> bytes:
    uid = uuid.UUID(user_id)

    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    resume = (await db.execute(
        select(Resume).where(Resume.user_id == uid, Resume.ats_score.isnot(None))
        .order_by(desc(Resume.created_at)).limit(1)
    )).scalar_one_or_none()
    latest_score = (await db.execute(
        select(CareerScore).where(CareerScore.user_id == uid)
        .order_by(desc(CareerScore.computed_at)).limit(1)
    )).scalar_one_or_none()
    quizzes = (await db.execute(
        select(QuizResult).where(QuizResult.user_id == uid, QuizResult.score.isnot(None))
        .order_by(desc(QuizResult.taken_at)).limit(5)
    )).scalars().all()
    interviews = (await db.execute(
        select(InterviewSession).where(InterviewSession.user_id == uid, InterviewSession.readiness_score.isnot(None))
        .order_by(desc(InterviewSession.created_at)).limit(3)
    )).scalars().all()
    plan = (await db.execute(
        select(StudyPlan).where(StudyPlan.user_id == uid, StudyPlan.is_active == True)
        .order_by(desc(StudyPlan.created_at)).limit(1)
    )).scalar_one_or_none()

    # Compute a fresh career score from available components
    resume_score = resume.ats_score if resume else None
    quiz_score = int(sum(q.score for q in quizzes) / len(quizzes)) if quizzes else None
    interview_score = interviews[0].readiness_score if interviews else None
    skill_score = latest_score.skill_score if latest_score else None
    cr = compute_career_readiness(
        resume_score=resume_score, skill_score=skill_score,
        quiz_score=quiz_score, interview_score=interview_score,
    )

    name = (user.name if user else "User") or "User"
    role = (user.target_role if user else "") or "Not set"
    today = datetime.now(timezone.utc).strftime("%d %B %Y")

    pdf = _Pdf()
    pdf.banner("AI Career Copilot — Career Readiness Report", f"{name}   ·   Target role: {role}   ·   {today}")

    # ── Overall score ──────────────────────────────────────────────────────────
    pdf.heading("Overall Career Readiness")
    pdf.score_box(cr.overall_score, cr.grade)
    if cr.message:
        pdf.text(cr.message, size=10.5, color=GREY)

    pdf.heading("Score Breakdown")
    pdf.kv_row("Resume (ATS)", f"{resume_score}/100" if resume_score is not None else "Not analysed yet")
    pdf.kv_row("Skills", f"{skill_score}/100" if skill_score is not None else "Run a skill gap analysis")
    pdf.kv_row("Quiz (avg)", f"{quiz_score}/100" if quiz_score is not None else "No quizzes taken")
    pdf.kv_row("Interview", f"{interview_score}/100" if interview_score is not None else "No mock interviews")

    # ── Resume snapshot ────────────────────────────────────────────────────────
    if resume:
        pdf.heading("Resume Snapshot")
        pdf.kv_row("File", resume.file_name or "—")
        skills = (resume.extracted_skills or [])[:18]
        if skills:
            pdf.text("Your skills: " + ", ".join(skills), size=10.5)
        missing = (resume.missing_skills or [])[:12]
        if missing:
            pdf.text("Skills to add: " + ", ".join(missing), size=10.5, color=GREEN)
        for s in (resume.suggestions or [])[:4]:
            pdf.bullet(s)

    # ── Recommendations ────────────────────────────────────────────────────────
    recs = (latest_score.recommendations if latest_score and latest_score.recommendations else cr.recommendations) or []
    if recs:
        pdf.heading("Priority Recommendations")
        for r in recs[:6]:
            pdf.bullet(r)
    if cr.next_milestone:
        pdf.text(f"Next milestone: {cr.next_milestone}", size=10.5, color=PRIMARY, bold=True)

    # ── Activity ───────────────────────────────────────────────────────────────
    pdf.heading("Activity Summary")
    pdf.kv_row("Quizzes taken", str(len(quizzes)))
    pdf.kv_row("Mock interviews", str(len(interviews)))
    pdf.kv_row("Active study plan", (plan.plan_type.title() + f" — {plan.target_role}") if plan else "None yet")

    # ── Footer note ────────────────────────────────────────────────────────────
    pdf.y = PAGE_H - MARGIN - 14
    pdf.text("Generated by AI Career Copilot — your agentic AI career platform.", size=9, color=GREY)

    logger.info(f"[ReportService] PDF generated | user={user_id} | overall={cr.overall_score}")
    return pdf.bytes()
