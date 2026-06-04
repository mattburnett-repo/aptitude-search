import sys
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


class AppConfig(BaseModel):
    title: str
    version: str
    service: str


class CorsConfig(BaseModel):
    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]


class LlmConfig(BaseModel):
    aptitude_model_key: str
    aptitude_model: str
    job_discovery_model_key: str
    job_discovery_model: str
    job_discovery_max_steps: int = 18
    temperature: float

    @field_validator(
        "aptitude_model_key",
        "job_discovery_model_key",
        "aptitude_model",
        "job_discovery_model",
    )
    @classmethod
    def llm_string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"llm.{field} must be set in config.toml")
        return stripped

    @field_validator("job_discovery_max_steps")
    @classmethod
    def job_discovery_max_steps_must_be_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("llm.job_discovery_max_steps must be at least 1")
        return value


class PromptsConfig(BaseModel):
    stage1_file: str
    stage2_file: str
    stage1_user_task_file: str = "stage1-agent-user-task.txt"
    stage2_user_task_file: str = "stage2-agent-user-task.txt"


class SchemasConfig(BaseModel):
    constraints: str
    aptitude_profile: str
    job_discovery_results: str


class PathsConfig(BaseModel):
    prompts_dir: str
    schemas_dir: str
    fixtures_example_outputs_dir: str


class FixtureValidateEntry(BaseModel):
    name: str
    stage: str


class FixturesConfig(BaseModel):
    files: list[FixtureValidateEntry] = Field(default_factory=list)


class Config(BaseModel):
    app: AppConfig
    cors: CorsConfig
    llm: LlmConfig
    prompts: PromptsConfig
    schemas: SchemasConfig
    paths: PathsConfig
    fixtures: FixturesConfig

    @classmethod
    def load(cls, path: Path = _CONFIG_PATH) -> "Config":
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)


try:
    config = Config.load()
except ValidationError as e:
    print(e)
    sys.exit(1)
