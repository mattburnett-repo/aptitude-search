"""Resume ingress: extract text from the request, then validate and sanitize."""

from __future__ import annotations

import base64
import binascii
from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader

from app.core.input_safety import prepare_resume
from app.core.models import Constraints, PipelineRequest
from app.core.progress import ProgressCallback, emit_progress


def extract_resume_text(
    body: PipelineRequest,
    *,
    on_progress: ProgressCallback | None = None,
) -> str:
    """Decode PDF upload or return pasted resume text (no safety checks)."""
    if body.resume_pdf_base64:
        emit_progress(
            "Extracting text from PDF resume…",
            on_progress=on_progress,
        )
        try:
            data = base64.b64decode(body.resume_pdf_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF upload encoding.",
            ) from exc
        resume = _extract_pdf_text(data)
        emit_progress("PDF text extracted.", on_progress=on_progress)
        return resume
    return body.resume


def ingest_resume(
    text: str,
    *,  # keyword-only: callers must pass on_progress=..., not positionally
    on_progress: ProgressCallback | None = None,
) -> str:
    """Require non-empty resume text, then run injection + PII safety."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    return prepare_resume(text, on_progress=on_progress)


def prepare_pipeline_inputs(
    body: PipelineRequest,
    *,
    on_progress: ProgressCallback | None = None,
) -> tuple[str, Constraints | None]:
    """Extract resume, validate/sanitize, return (resume, constraints) for run_pipeline."""
    resume = ingest_resume(
        extract_resume_text(body, on_progress=on_progress),
        on_progress=on_progress,
    )
    return resume, body.constraints


def _extract_pdf_text(data: bytes) -> str:
    """Extract plain text from PDF bytes (pypdf)."""
    if not data:
        raise HTTPException(status_code=400, detail="resume file is empty")

    try:
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF resume.",
        ) from exc

    text = "\n\n".join(pages).strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the PDF resume.",
        )
    return text
