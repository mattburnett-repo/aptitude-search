import base64
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.models import PipelineRequest
from app.core.resume_io import (
    _extract_pdf_text,  # pyright: ignore[reportPrivateUsage]
    extract_resume_text,
    ingest_resume,
    prepare_pipeline_inputs,
)


def test_extract_resume_text_returns_plain_resume_text():
    body = PipelineRequest(resume="Jane Doe\nEngineer")
    assert extract_resume_text(body) == "Jane Doe\nEngineer"


def test_extract_resume_text_rejects_invalid_pdf_base64():
    body = PipelineRequest(resume="", resume_pdf_base64="not-valid-base64!!")
    with pytest.raises(HTTPException) as exc:
        _ = extract_resume_text(body)
    assert exc.value.status_code == 400
    assert "Invalid PDF upload encoding" in str(exc.value.detail)


def test_extract_pdf_text_rejects_empty_bytes():
    with pytest.raises(HTTPException) as exc:
        _ = _extract_pdf_text(b"")
    assert exc.value.status_code == 400
    assert "empty" in str(exc.value.detail).lower()


@patch("app.core.resume_io.PdfReader")
def test_extract_pdf_text_returns_joined_page_text(mock_reader: MagicMock):
    reader = cast(MagicMock, mock_reader.return_value)
    reader.pages = [
        SimpleNamespace(extract_text=lambda: "Jane Doe"),
        SimpleNamespace(extract_text=lambda: "Software Engineer"),
    ]

    text = _extract_pdf_text(b"%PDF-1.4 fake")
    assert text == "Jane Doe\n\nSoftware Engineer"


@patch("app.core.resume_io._extract_pdf_text", return_value="Extracted resume text")
def test_extract_resume_text_decodes_pdf_base64(mock_extract: MagicMock):
    encoded = base64.b64encode(b"%PDF-fake").decode()
    body = PipelineRequest(resume="", resume_pdf_base64=encoded)
    assert extract_resume_text(body) == "Extracted resume text"
    mock_extract.assert_called_once()


def test_ingest_resume_rejects_empty():
    with pytest.raises(HTTPException) as exc:
        _ = ingest_resume("   ")
    assert exc.value.status_code == 400
    assert exc.value.detail == "resume is required"


@patch("app.core.resume_io.prepare_resume", return_value="safe resume")
def test_ingest_resume_calls_prepare(mock_prepare: MagicMock):
    assert ingest_resume("Jane Doe\nEngineer") == "safe resume"
    mock_prepare.assert_called_once()


@patch("app.core.resume_io.prepare_resume", return_value="safe resume")
def test_prepare_pipeline_inputs_returns_constraints(mock_prepare: MagicMock):
    body = PipelineRequest(resume="Jane Doe", constraints=None)
    resume, constraints = prepare_pipeline_inputs(body)
    assert resume == "safe resume"
    assert constraints is None
    mock_prepare.assert_called_once()
