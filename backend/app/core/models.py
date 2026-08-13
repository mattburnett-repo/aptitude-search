import json
from pathlib import Path
from typing import ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from app.core.json_types import JsonObject

_FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures"
_PIPELINE_EXAMPLE_PATH = _FIXTURES_DIR / "pipeline-request-example.json"
_PIPELINE_EXAMPLE_RESUME_PATH = (
    _FIXTURES_DIR / "sample-resumes" / "civic-climate-product-engineer.txt"
)


def _load_pipeline_request_example() -> JsonObject:
    """Swagger Try It Out body: constraints from JSON, resume from the sample txt."""
    example = cast(JsonObject, json.loads(_PIPELINE_EXAMPLE_PATH.read_text(encoding="utf-8")))
    example["resume"] = _PIPELINE_EXAMPLE_RESUME_PATH.read_text(encoding="utf-8")
    return example


class Constraints(BaseModel):
    location: str = ""
    remote_preference: Literal["remote", "hybrid", "onsite", "any"] = "any"
    salary_min: float | None = None
    industries_include: list[str] = Field(default_factory=list)
    industries_exclude: list[str] = Field(default_factory=list)


def _pipeline_request_openapi_example(schema: dict[str, object]) -> None:
    schema["examples"] = [_load_pipeline_request_example()]


class PipelineRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        json_schema_extra=_pipeline_request_openapi_example,  # pyright: ignore[reportArgumentType]
    )

    resume: str = ""
    resume_pdf_base64: str | None = None  # Base64 PDF from frontend; decoded and extracted server-side
    constraints: Constraints | None = None


class Stage1Request(BaseModel):
    resume: str


class Stage2Request(BaseModel):
    aptitude_profile: dict[str, object]


class Stage3Request(BaseModel):
    aptitude_profile: dict[str, object]
    role_family_plan: dict[str, object] | None = None
    constraints: Constraints | None = None
