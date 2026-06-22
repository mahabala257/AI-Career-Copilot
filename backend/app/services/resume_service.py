"""
app/services/resume_service.py
────────────────────────────────
Business logic layer for all resume operations.

Why a service layer between routes and agents?
  - Routes handle HTTP (request parsing, response shaping, status codes)
  - Agents handle AI (LLM calls, state management)
  - Services handle business logic (DB reads/writes, file storage,
    orchestrating the two layers above)

  Without this layer, routes become 200-line monsters mixing HTTP, DB,
  and AI logic. With it, each layer has one responsibility.

What this service does:
  1. save_resume_file()     — persist uploaded PDF to disk, return file path
  2. run_resume_analysis()  — invoke LangGraph with resume state, persist results
  3. get_resume_history()   — fetch past analyses from DB for a user
  4. get_resume_by_id()     — fetch one analysis record
  5. build_resume_state()   — construct the LangGraph state dict for resume requests
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import career_copilot_graph
from app.agents.state import AgentName, create_initial_state
from app.config import settings
from app.models.models import Resume
from app.services.pdf_service import ParsedResume, extract_resume_text

logger = logging.getLogger(__name__)


# ── File storage ───────────────────────────────────────────────────────────────

async def save_resume_file(
    file_bytes: bytes,
    original_filename: str,
    user_id: str,
) -> tuple[str, str]:
    """
    Save uploaded PDF to disk under uploads/{user_id}/.
    Returns (file_path, stored_filename).

    We store under user subdirectory so files are isolated per user,
    and use a UUID prefix to prevent filename collisions.
    """
    user_upload_dir = Path(settings.upload_dir) / user_id
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    # UUID prefix prevents overwriting if the same name is re-uploaded
    safe_name = f"{uuid.uuid4().hex[:8]}_{original_filename}"
    file_path = user_upload_dir / safe_name

    # aiofiles would be cleaner but for robustness we use sync write here
    # (FastAPI runs the route in a thread pool when using UploadFile)
    file_path.write_bytes(file_bytes)

    logger.info(f"[ResumeService] Saved file: {file_path} ({len(file_bytes)} bytes)")
    return str(file_path), safe_name


async def run_resume_analysis(
    *,
    file_bytes: bytes,
    filename: str,
    user_id: str,
    session_id: str,
    target_role: str,
    db: AsyncSession,
) -> dict:
    """
    Full resume analysis pipeline:
      1. Parse PDF → extract text
      2. Save file to disk
      3. Create DB record (pre-analysis)
      4. Run LangGraph Resume Agent
      5. Update DB record with analysis results
      6. Return structured response

    Returns a dict matching ResumeAnalysisResponse schema.
    """

    # ── Step 1: Parse PDF ──────────────────────────────────────────────────────
    logger.info(f"[ResumeService] Parsing PDF: {filename}")
    parsed: ParsedResume = await extract_resume_text(file_bytes, filename)

    if not parsed.has_content:
        raise ValueError(
            "Could not extract text from this PDF. "
            "It may be a scanned image. Please use a text-based PDF."
        )

    # ── Step 2: Save file ──────────────────────────────────────────────────────
    file_path, stored_name = await save_resume_file(file_bytes, filename, user_id)

    # ── Step 3: Create DB record ───────────────────────────────────────────────
    resume_record = Resume(
        user_id=uuid.UUID(user_id),
        file_name=filename,
        file_path=file_path,
        raw_text=parsed.raw_text,
        # Analysis fields populated after agent runs
    )
    db.add(resume_record)
    await db.flush()  # Get the ID before the agent runs
    resume_id = str(resume_record.id)

    logger.info(f"[ResumeService] Resume record created: {resume_id}")

    # ── Step 4: Run LangGraph ──────────────────────────────────────────────────
    initial_state = create_initial_state(
        user_id=user_id,
        session_id=session_id,
        user_message=f"Analyze my resume for the role: {target_role}",
        target_role=target_role,
        resume_text=parsed.truncated_text,
    )

    logger.info(f"[ResumeService] Invoking LangGraph Resume Agent")
    result = await career_copilot_graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": session_id}},
    )

    analysis = result.get("resume_analysis", {})
    error = result.get("error")

    # ── Step 5: Persist analysis results ──────────────────────────────────────
    resume_record.ats_score         = analysis.get("ats_score")
    resume_record.extracted_skills  = analysis.get("extracted_skills", [])
    resume_record.missing_skills    = analysis.get("missing_skills", [])
    resume_record.suggestions       = analysis.get("suggestions", [])
    resume_record.strengths         = analysis.get("strengths", [])
    resume_record.analyzed_at       = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(resume_record)

    logger.info(
        f"[ResumeService] Analysis complete | "
        f"resume_id={resume_id} | ats_score={analysis.get('ats_score')}"
    )

    # ── Step 6: Return structured response ────────────────────────────────────
    return {
        "resume_id":       resume_id,
        "filename":        filename,
        "page_count":      parsed.page_count,
        "word_count":      parsed.word_count,
        "sections":        parsed.sections_detected,
        "analysis":        analysis,
        "parse_warnings":  parsed.parse_warnings,
        "agent_error":     error,
        "analyzed_at":     resume_record.analyzed_at.isoformat(),
    }


async def get_resume_history(
    user_id: str,
    db: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """
    Fetch all resume analyses for a user, newest first.
    Used by the Resume History page.
    """
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == uuid.UUID(user_id))
        .order_by(desc(Resume.created_at))
        .limit(limit)
    )
    resumes = result.scalars().all()

    return [
        {
            "resume_id":    str(r.id),
            "filename":     r.file_name,
            "ats_score":    r.ats_score,
            "analyzed_at":  r.analyzed_at.isoformat() if r.analyzed_at else None,
            "created_at":   r.created_at.isoformat(),
            "skills_count": len(r.extracted_skills or []),
            "missing_count": len(r.missing_skills or []),
        }
        for r in resumes
    ]


async def get_resume_by_id(
    resume_id: str,
    user_id: str,
    db: AsyncSession,
) -> Optional[dict]:
    """
    Fetch one resume record by ID. Enforces user ownership.
    Returns None if not found or doesn't belong to user.
    """
    result = await db.execute(
        select(Resume).where(
            Resume.id      == uuid.UUID(resume_id),
            Resume.user_id == uuid.UUID(user_id),
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        return None

    return {
        "resume_id":        str(r.id),
        "filename":         r.file_name,
        "ats_score":        r.ats_score,
        "extracted_skills": r.extracted_skills or [],
        "missing_skills":   r.missing_skills or [],
        "suggestions":      r.suggestions or [],
        "strengths":        r.strengths or [],
        "analyzed_at":      r.analyzed_at.isoformat() if r.analyzed_at else None,
        "created_at":       r.created_at.isoformat(),
        "raw_text_preview": (r.raw_text or "")[:500],
    }
