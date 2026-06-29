"""
app/services/pdf_service.py
────────────────────────────
PDF text extraction service using PyMuPDF (fitz).

Why PyMuPDF over other options?
  - pdfplumber: slower, heavier dependency, better for tables
  - pypdf2/pypdf: pure Python, struggles with scanned/complex layouts
  - PyMuPDF: C extension, extremely fast, handles most real-world PDFs,
    preserves reading order, handles multi-column layouts better

What this service does
───────────────────────
  1. Validates the file is actually a PDF (not just a renamed .txt)
  2. Extracts text page by page, preserving paragraph structure
  3. Cleans common PDF extraction artifacts (ligatures, broken hyphens,
     excessive whitespace, header/footer noise)
  4. Extracts basic metadata (page count, title if embedded)
  5. Returns a structured ParsedResume object

Why clean the text?
────────────────────
Raw PDF text from PyMuPDF often contains:
  - Ligatures: "ﬁ" instead of "fi", "ﬂ" instead of "fl"
  - Line-break hyphens: "Develop-\nment" → "Development"
  - Multiple spaces from column layout
  - Page numbers and headers bleeding into content

Gemini handles dirty text OK, but clean text → better token efficiency
and more accurate skill extraction.
"""

import io
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Maximum resume text we send to Gemini (tokens cost money).
# Real resumes are rarely over 3000 words — 8000 chars is generous.
MAX_RESUME_CHARS = 8000


@dataclass
class ParsedResume:
    """Structured result from PDF parsing."""
    raw_text: str               # Full extracted text (cleaned)
    truncated_text: str         # Text capped at MAX_RESUME_CHARS for LLM
    page_count: int
    char_count: int
    word_count: int
    has_content: bool
    title: Optional[str] = None
    sections_detected: list[str] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)


class PDFParseError(Exception):
    """Raised when PDF cannot be parsed."""
    pass


async def extract_resume_text(
    file_bytes: bytes,
    filename: str = "resume.pdf",
) -> ParsedResume:
    """
    Main entry point. Extract and clean text from a resume PDF.

    Args:
        file_bytes: Raw bytes of the uploaded PDF file
        filename: Original filename (used for error messages)

    Returns:
        ParsedResume with cleaned text and metadata

    Raises:
        PDFParseError: If the file is not a valid PDF or is unreadable
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise PDFParseError(
            "PyMuPDF not installed. Run: pip install PyMuPDF"
        )

    # ── Validate it's actually a PDF ───────────────────────────────────────────
    if len(file_bytes) < 5 or file_bytes[:4] != b"%PDF":
        raise PDFParseError(
            f"File '{filename}' does not appear to be a valid PDF. "
            "Please upload a PDF file."
        )

    warnings = []

    try:
        # Open from bytes (no temp file needed)
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise PDFParseError(f"Could not open PDF '{filename}': {e}")

    page_count = len(pdf)
    if page_count == 0:
        raise PDFParseError(f"PDF '{filename}' has no pages.")

    # ── Extract text page by page ──────────────────────────────────────────────
    pages_text = []
    for page_num in range(page_count):
        try:
            page = pdf[page_num]
            # "text" mode preserves reading order better than raw extraction.
            # "blocks" mode is better for tables but we don't need that here.
            text = page.get_text("text")
            pages_text.append(text)
        except Exception as e:
            warnings.append(f"Could not extract page {page_num + 1}: {e}")
            pages_text.append("")

    # ── Get embedded metadata ──────────────────────────────────────────────────
    metadata = pdf.metadata or {}
    title = metadata.get("title") or metadata.get("Title") or None
    pdf.close()

    # ── Join and clean ─────────────────────────────────────────────────────────
    full_text = "\n".join(pages_text)
    cleaned = _clean_resume_text(full_text)

    if len(cleaned.strip()) < 50:
        # Very little text — probably a scanned PDF with no OCR
        warnings.append(
            "Very little text was extracted. This may be a scanned resume "
            "without embedded text. OCR support is not yet available."
        )

    # ── Detect sections for metadata ──────────────────────────────────────────
    sections = _detect_sections(cleaned)

    # ── Build result ───────────────────────────────────────────────────────────
    word_count = len(cleaned.split())
    truncated = cleaned[:MAX_RESUME_CHARS]
    if len(cleaned) > MAX_RESUME_CHARS:
        warnings.append(
            f"Resume text truncated to {MAX_RESUME_CHARS} characters for analysis "
            f"(original: {len(cleaned)} chars)."
        )

    logger.info(
        f"[PDF] Parsed '{filename}': {page_count} pages, "
        f"{word_count} words, {len(sections)} sections detected"
    )

    return ParsedResume(
        raw_text=cleaned,
        truncated_text=truncated,
        page_count=page_count,
        char_count=len(cleaned),
        word_count=word_count,
        has_content=len(cleaned.strip()) >= 50,
        title=title,
        sections_detected=sections,
        parse_warnings=warnings,
    )


def _clean_resume_text(raw: str) -> str:
    """
    Clean common PDF extraction artifacts from resume text.

    Operations (in order):
      1. Fix Unicode ligatures (ﬁ→fi, ﬂ→fl, etc.)
      2. Fix hyphenated line breaks ("Develop-\nment" → "Development")
      3. Normalize whitespace (tabs, multiple spaces → single space)
      4. Remove lines that are purely decorative (dashes, underscores)
      5. Remove common header/footer patterns (page numbers)
      6. Collapse multiple blank lines to max 2
    """
    text = raw

    # 1. Fix ligatures
    ligatures = {
        "\ufb01": "fi",   # ﬁ
        "\ufb02": "fl",   # ﬂ
        "\ufb03": "ffi",  # ﬃ
        "\ufb04": "ffl",  # ﬄ
        "\ufb00": "ff",   # ﬀ
        "\u2019": "'",    # right single quotation
        "\u2018": "'",    # left single quotation
        "\u201c": '"',    # left double quotation
        "\u201d": '"',    # right double quotation
        "\u2013": "-",    # en dash
        "\u2014": "--",   # em dash
        "\u00a0": " ",    # non-breaking space
    }
    for char, replacement in ligatures.items():
        text = text.replace(char, replacement)

    # 2. Fix hyphenated line breaks: "develop-\nment" → "development"
    text = re.sub(r"-\n(\w)", lambda m: m.group(1), text)

    # 3. Normalize whitespace within lines (preserve newlines)
    lines = text.split("\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]

    # 4. Remove purely decorative lines
    lines = [
        line for line in lines
        if not re.match(r"^[-_=|*•·▪▸►»]+$", line)
    ]

    # 5. Remove page number lines (common patterns)
    lines = [
        line for line in lines
        if not re.match(r"^(page\s+)?\d+(\s+of\s+\d+)?$", line, re.IGNORECASE)
    ]

    # 6. Remove very short lines that are just single characters or noise
    # (but keep single-word lines — they might be section headers)
    lines = [line for line in lines if len(line) != 1]

    text = "\n".join(lines)

    # 7. Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _detect_sections(text: str) -> list[str]:
    """
    Detect common resume sections to help with parsing metadata.
    Returns list of section names found (for diagnostic purposes).
    """
    section_patterns = {
        "Education":    r"\b(education|academics|qualification)\b",
        "Experience":   r"\b(experience|employment|work history|internship)\b",
        "Skills":       r"\b(skills|technical skills|core competencies|technologies)\b",
        "Projects":     r"\b(projects|personal projects|academic projects)\b",
        "Summary":      r"\b(summary|objective|profile|about me)\b",
        "Certifications": r"\b(certifications|certificates|credentials)\b",
        "Achievements": r"\b(achievements|awards|honors|accomplishments)\b",
    }

    text_lower = text.lower()
    detected = []
    for section_name, pattern in section_patterns.items():
        if re.search(pattern, text_lower):
            detected.append(section_name)

    return detected


def validate_resume_file(
    filename: str,
    file_size_bytes: int,
    max_size_bytes: int,
) -> Optional[str]:
    """
    Validate file before parsing. Returns error message or None if valid.
    Called by the API route before any processing.
    """
    # Check extension
    suffix = Path(filename).suffix.lower()
    if suffix != ".pdf":
        return f"Only PDF files are accepted. Received: '{suffix}' file."

    # Check size
    if file_size_bytes > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        actual_mb = file_size_bytes / (1024 * 1024)
        return (
            f"File size ({actual_mb:.1f} MB) exceeds the {max_mb:.0f} MB limit. "
            "Please compress or trim your resume."
        )

    if file_size_bytes < 100:
        return "File appears to be empty or corrupted."

    return None  # Valid
