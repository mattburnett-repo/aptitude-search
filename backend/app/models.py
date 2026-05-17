from typing import Any, Literal

from pydantic import BaseModel, Field


class Constraints(BaseModel):
    location: str = ""
    remote_preference: Literal["remote", "hybrid", "onsite", "any"] = "any"
    salary_min: float | None = None
    industries_include: list[str] = Field(default_factory=list)
    industries_exclude: list[str] = Field(default_factory=list)


class PipelineRequest(BaseModel):
    resume: str
    constraints: Constraints | None = None


class Stage1Request(BaseModel):
    resume: str


class Stage2Request(BaseModel):
    aptitude_profile: Any
    constraints: Constraints | None = None
