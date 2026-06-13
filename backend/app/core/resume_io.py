import base64
import binascii
from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader

from app.core.models import Constraints, PipelineRequest
from app.core.progress import ProgressCallback, emit_progress


def parse_pipeline_body(
    body: PipelineRequest,
    *,
    on_progress: ProgressCallback | None = None,
) -> tuple[str, Constraints | None]:
    """Return plain resume text. PDF uploads arrive as resume_pdf_base64."""
    if body.resume_pdf_base64:
        emit_progress(
            "Extracting text from PDF resume…",
            on_progress=on_progress,
        )
        # Frontend sends PDF as base64 JSON; decode and extract text here.
        try:
            data = base64.b64decode(body.resume_pdf_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF upload encoding.",
            ) from exc
        resume = _extract_pdf_text(data)
        emit_progress("PDF text extracted.", on_progress=on_progress)
    else:
        resume = body.resume

    return resume, body.constraints


def _extract_pdf_text(data: bytes) -> str:
    """Extract plain text from PDF bytes (pypdf). Pipeline always receives a string."""
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
