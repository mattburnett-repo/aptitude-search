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


class AptitudeLlmConfig(BaseModel):
    model_key: str
    model: str
    temperature: float

    @field_validator("model_key", "model")
    @classmethod
    def string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"llm.aptitude.{field} must be set in config.toml")
        return stripped


class JobDiscoveryConfig(BaseModel):
    url_filters_file: str = "url-filters.toml"


class JobDiscoveryLlmConfig(BaseModel):
    model_key: str
    model: str
    temperature: float
    max_steps: int
    visit_max_output_length: int
    search_max_results: int
    search_snippet_max_chars: int
    search_rate_limit: float | None
    max_print_outputs_length: int
    page_summary_max_chars: int
    page_bullet_max_count: int
    page_snippet_max_chars: int
    memory_keep_recent_steps: int
    memory_pruned_observation_max_chars: int

    @field_validator("model_key", "model")
    @classmethod
    def string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"llm.job_discovery.{field} must be set in config.toml")
        return stripped

    @field_validator(
        "max_steps",
        "visit_max_output_length",
        "search_max_results",
        "search_snippet_max_chars",
        "max_print_outputs_length",
        "page_summary_max_chars",
        "page_bullet_max_count",
        "page_snippet_max_chars",
        "memory_keep_recent_steps",
        "memory_pruned_observation_max_chars",
    )
    @classmethod
    def positive_int(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"llm.job_discovery.{field} must be at least 1")
        return value

    @field_validator("search_rate_limit")
    @classmethod
    def search_rate_limit_positive(
        cls, value: float | None, info: ValidationInfo
    ) -> float | None:
        if value is not None and value <= 0:
            field = info.field_name or "field"
            raise ValueError(
                f"llm.job_discovery.{field} must be positive or omitted (null) to disable"
            )
        return value


class LlmConfig(BaseModel):
    aptitude: AptitudeLlmConfig
    job_discovery: JobDiscoveryLlmConfig


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
    job_discovery: JobDiscoveryConfig = Field(default_factory=JobDiscoveryConfig)
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
