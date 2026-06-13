import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

_PIPELINE_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "pipeline-request-example.json"
)


def _load_pipeline_request_example() -> dict:
    return json.loads(_PIPELINE_EXAMPLE_PATH.read_text(encoding="utf-8"))


class Constraints(BaseModel):
    location: str = ""
    remote_preference: Literal["remote", "hybrid", "onsite", "any"] = "any"
    salary_min: float | None = None
    industries_include: list[str] = Field(default_factory=list)
    industries_exclude: list[str] = Field(default_factory=list)


class PipelineRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [_load_pipeline_request_example()]}
    )

    resume: str = ""
    resume_pdf_base64: str | None = None  # Base64 PDF from frontend; decoded and extracted server-side
    constraints: Constraints | None = None


class Stage1Request(BaseModel):
    resume: str


class Stage2Request(BaseModel):
    aptitude_profile: Any
    constraints: Constraints | None = None
