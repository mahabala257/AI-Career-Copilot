"""
app/api/routes/resume.py
─────────────────────────
Resume API endpoints.

Endpoints:
  POST /api/resume/upload-and-analyze  — Upload PDF + run full analysis in one call
  GET  /api/resume/history             — List all past analyses for the current user
  GET  /api/resume/{resume_id}         — Get one specific analysis by ID

Design decisions:
  - We combine upload + analyze into one endpoint instead of two separate steps.
    The frontend sends the file and gets back the full analysis. This is simpler
    UX and avoids the race condition of "file uploaded but analysis not started yet".

  - File validation happens BEFORE any DB or AI work. If the file is invalid,
    we return 400 immediately without wasting tokens or storage.

  - All AI errors are surfaced in the response body (not as HTTP 500) so the
    frontend can show a user-friendly message rather than a generic error screen.

  - JWT authentication is required for all endpoints — users can only see
    their own resumes (enforced in the service layer by user_id filtering).
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.resume import (
    ResumeAnalysisResponse,
    ResumeDetailResponse,
    ResumeHistoryResponse,
)
from app.services.resume_service import (
    get_resume_by_id,
    get_resume_history,
    run_resume_analysis,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resume", tags=["Resume"])


# ── Upload + Analyze ───────────────────────────────────────────────────────────
@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload resume PDF and run AI analysis",
    description=(
        "Upload a resume PDF and receive a full ATS analysis including skill extraction, "
        "missing skills detection, score breakdown, and improvement suggestions. "
        "Powered by Gemini 2.0 Flash + ChromaDB RAG."
    ),
)
async def upload_and_analyze_resume(
    file: UploadFile = File(..., description="Resume PDF file (max 10 MB)"),
    target_role: str = Form(
        ...,
        description="Target job role, e.g. 'AI Engineer' or 'Data Scientist'",
        min_length=2,
        max_length=100,
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeAnalysisResponse:
    """
    Workflow:
      1. Validate filename extension
      2. Read bytes (single pass — size is checked post-read so file.size=None is safe)
      3. Validate actual size and PDF magic bytes
      4. Service: parse PDF → extract text → run agent → persist → return
    """
    filename = file.filename or "resume.pdf"

    # ── Extension check (cheap, pre-read) ─────────────────────────────────────
    # Only validate extension here. Size and MIME are validated post-read because
    # file.size is unreliable (None when Content-Length header is absent), and
    # reading the file is required to check magic bytes anyway.
    import re as _re
    from pathlib import Path as _Path
    if _Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # Reject obviously wrong content types (some browsers send octet-stream, allow it).
    if file.content_type and file.content_type not in ("application/pdf", "application/octet-stream", ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # Sanitize the filename to a safe basename (prevents path traversal when the
    # file is written to disk by the service).
    filename = _re.sub(r"[^A-Za-z0-9._-]", "_", _Path(filename).name)[:120] or "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    # ── Read file bytes ────────────────────────────────────────────────────────
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {e}",
        )

    # ── ISSUE-07 FIX: size check on actual bytes (not the unreliable file.size) ─
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File is too large ({len(file_bytes) / 1024 / 1024:.1f} MB). "
                f"Maximum allowed: {settings.max_upload_size_mb} MB."
            ),
        )

    if len(file_bytes) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File appears to be empty or corrupted.",
        )

    # ── ISSUE-08 FIX: PDF magic byte check ────────────────────────────────────
    # Reject files that have a .pdf extension but are not actually PDF.
    # A valid PDF always starts with the 4-byte sequence b"%PDF".
    if file_bytes[:4] != b"%PDF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The uploaded file does not appear to be a valid PDF "
                "(failed magic byte check). Please upload a genuine PDF file."
            ),
        )

    logger.info(
        f"[ResumeRoute] Upload | user={current_user.id} | "
        f"file={filename} | size={len(file_bytes)} bytes | role={target_role}"
    )

    # ── Run analysis ───────────────────────────────────────────────────────────
    # All business logic (PDF parsing, agent invocation, DB persistence)
    # is in the service layer — the route stays thin.
    try:
        result = await run_resume_analysis(
            file_bytes=file_bytes,
            filename=filename,
            user_id=str(current_user.id),
            session_id=str(current_user.id),  # Use user ID as session for stateful memory
            target_role=target_role,
            db=db,
        )
    except ValueError as e:
        # User-facing errors (bad PDF, no text, etc.)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[ResumeRoute] Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume analysis failed. Please try again.",
        )

    # Pydantic validates the response shape here automatically
    return ResumeAnalysisResponse(**result)


# ── History ────────────────────────────────────────────────────────────────────
@router.get(
    "/history",
    response_model=ResumeHistoryResponse,
    summary="Get all past resume analyses for the current user",
)
async def get_resume_history_endpoint(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeHistoryResponse:
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 50",
        )

    items = await get_resume_history(
        user_id=str(current_user.id),
        db=db,
        limit=limit,
    )
    return ResumeHistoryResponse(items=items, total=len(items))


# ── Get by ID ──────────────────────────────────────────────────────────────────
@router.get(
    "/{resume_id}",
    response_model=ResumeDetailResponse,
    summary="Get a specific resume analysis by ID",
)
async def get_resume_detail(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeDetailResponse:
    result = await get_resume_by_id(
        resume_id=resume_id,
        user_id=str(current_user.id),
        db=db,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume '{resume_id}' not found.",
        )
    return ResumeDetailResponse(**result)
