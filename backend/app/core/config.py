import sys
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.toml"


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
    job_discovery_max_steps: int
    job_discovery_visit_max_output_length: int
    job_discovery_search_max_results: int
    job_discovery_search_snippet_max_chars: int
    job_discovery_search_rate_limit: float | None
    job_discovery_max_print_outputs_length: int
    job_discovery_page_summary_max_chars: int
    job_discovery_page_bullet_max_count: int
    job_discovery_page_snippet_max_chars: int
    job_discovery_memory_keep_recent_steps: int
    job_discovery_memory_pruned_observation_max_chars: int
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

    @field_validator(
        "job_discovery_max_steps",
        "job_discovery_visit_max_output_length",
        "job_discovery_search_max_results",
        "job_discovery_search_snippet_max_chars",
        "job_discovery_max_print_outputs_length",
        "job_discovery_page_summary_max_chars",
        "job_discovery_page_bullet_max_count",
        "job_discovery_page_snippet_max_chars",
        "job_discovery_memory_keep_recent_steps",
        "job_discovery_memory_pruned_observation_max_chars",
    )
    @classmethod
    def job_discovery_positive_int(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"llm.{field} must be at least 1")
        return value

    @field_validator("job_discovery_search_rate_limit")
    @classmethod
    def job_discovery_search_rate_limit_positive(
        cls, value: float | None, info: ValidationInfo
    ) -> float | None:
        if value is not None and value <= 0:
            field = info.field_name or "field"
            raise ValueError(f"llm.{field} must be positive or omitted (null) to disable")
        return value


class PromptsConfig(BaseModel):
    stage1_file: str
    stage2_discovery_file: str
    stage2_synthesis_file: str
    code_agent_file: str
    stage1_user_task_file: str = "stage1-agent-user-task.txt"
    stage2_user_task_file: str = "stage2-agent-user-task.txt"
    stage2_synthesis_user_task_file: str = "stage2-synthesis-user-task.txt"


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
        """Read config.toml and build the typed Config object (all settings load here)."""
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)


try:
    config = Config.load()
except ValidationError as e:
    print(e)
    sys.exit(1)
