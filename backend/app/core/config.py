import sys
import tomllib
from pathlib import Path
from typing import Literal

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
    max_tokens: int = 8192

    @field_validator("model_key", "model")
    @classmethod
    def string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"llm.aptitude.{field} must be set in config.toml")
        return stripped

    @field_validator("max_tokens")
    @classmethod
    def max_tokens_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 256:
            field = info.field_name or "field"
            raise ValueError(f"llm.aptitude.{field} must be at least 256")
        return value


_TavilySearchDepth = Literal["basic", "advanced", "fast", "ultra-fast"]


class JobDiscoveryConfig(BaseModel):
    url_filters_file: str
    discovery_query_max: int
    tavily_api_key: str
    result_top_k: int = 25
    search_depth: _TavilySearchDepth = "basic"
    search_min_score: float = 0.0

    @field_validator("url_filters_file")
    @classmethod
    def url_filters_file_basename(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"job_discovery.{field} must be set in config.toml")
        if Path(stripped).name != stripped or stripped in (".", ".."):
            raise ValueError(
                "job_discovery.url_filters_file must be a filename under app/job_discovery/"
            )
        return stripped

    @field_validator("discovery_query_max")
    @classmethod
    def discovery_query_max_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"job_discovery.{field} must be at least 1")
        return value

    @field_validator("tavily_api_key")
    @classmethod
    def tavily_api_key_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"job_discovery.{field} must be set in config.toml")
        return stripped

    @field_validator("result_top_k")
    @classmethod
    def result_top_k_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"job_discovery.{field} must be at least 1")
        return value

    @field_validator("search_min_score")
    @classmethod
    def search_min_score_in_range(cls, value: float, info: ValidationInfo) -> float:
        if value < 0.0 or value > 1.0:
            field = info.field_name or "field"
            raise ValueError(f"job_discovery.{field} must be between 0 and 1")
        return value


class InputGuardLlmConfig(BaseModel):
    model_key: str
    model: str
    chunk_max_chars: int = 1800
    malicious_score_threshold: float = 0.5

    @field_validator("model_key", "model")
    @classmethod
    def string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"llm.input_guard.{field} must be set in config.toml")
        return stripped

    @field_validator("chunk_max_chars")
    @classmethod
    def chunk_max_chars_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 256:
            field = info.field_name or "field"
            raise ValueError(f"llm.input_guard.{field} must be at least 256")
        return value

    @field_validator("malicious_score_threshold")
    @classmethod
    def malicious_score_threshold_in_range(
        cls, value: float, info: ValidationInfo
    ) -> float:
        if value < 0.0 or value > 1.0:
            field = info.field_name or "field"
            raise ValueError(f"llm.input_guard.{field} must be between 0 and 1")
        return value


class InputSafetyConfig(BaseModel):
    max_resume_chars: int = 100_000
    pii_entities: list[str] = Field(
        default_factory=lambda: [
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "PERSON",
            "LOCATION",
            "US_SSN",
        ]
    )

    @field_validator("max_resume_chars")
    @classmethod
    def max_resume_chars_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"input_safety.{field} must be at least 1")
        return value


class JobDiscoveryLlmConfig(BaseModel):
    model_key: str
    model: str
    temperature: float
    max_tokens: int = 8192
    search_max_results: int
    search_snippet_max_chars: int
    search_rate_limit: float | None

    @field_validator("model_key", "model")
    @classmethod
    def string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"llm.job_discovery.{field} must be set in config.toml")
        return stripped

    @field_validator("max_tokens")
    @classmethod
    def max_tokens_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 256:
            field = info.field_name or "field"
            raise ValueError(f"llm.job_discovery.{field} must be at least 256")
        return value

    @field_validator("search_max_results", "search_snippet_max_chars")
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


class EmbeddingConfig(BaseModel):
    model_key: str
    model: str
    dimensions: int

    @field_validator("model_key", "model")
    @classmethod
    def string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"embedding.{field} must be set in config.toml")
        return stripped

    @field_validator("dimensions")
    @classmethod
    def dimensions_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"embedding.{field} must be at least 1")
        return value


class OnetMatchingConfig(BaseModel):
    enabled: bool
    top_k: int
    min_similarity: float

    @field_validator("top_k")
    @classmethod
    def top_k_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"onet_matching.{field} must be at least 1")
        return value

    @field_validator("min_similarity")
    @classmethod
    def min_similarity_in_range(cls, value: float, info: ValidationInfo) -> float:
        if value < 0.0 or value > 1.0:
            field = info.field_name or "field"
            raise ValueError(f"onet_matching.{field} must be between 0 and 1")
        return value


class OnetConfig(BaseModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    sslmode: str = "require"

    @field_validator("host", "database", "user", "password")
    @classmethod
    def string_must_be_set(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            field = info.field_name or "field"
            raise ValueError(f"onet.{field} must be set in config.toml")
        return stripped

    @field_validator("port")
    @classmethod
    def port_positive(cls, value: int, info: ValidationInfo) -> int:
        if value < 1:
            field = info.field_name or "field"
            raise ValueError(f"onet.{field} must be at least 1")
        return value

    def conninfo(self) -> str:
        from psycopg.conninfo import make_conninfo

        return make_conninfo(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.user,
            password=self.password,
            sslmode=self.sslmode,
        )


class LlmConfig(BaseModel):
    aptitude: AptitudeLlmConfig
    job_discovery: JobDiscoveryLlmConfig
    input_guard: InputGuardLlmConfig


class PromptsConfig(BaseModel):
    stage1_file: str
    stage2_file: str
    stage3_synthesis_file: str
    stage1_user_task_file: str
    stage2_user_task_file: str
    stage3_synthesis_user_task_file: str


class SchemasConfig(BaseModel):
    constraints: str
    aptitude_profile: str
    role_family_plan: str
    job_discovery_results: str
    input_guard: str


class PathsConfig(BaseModel):
    prompts_dir: str
    schemas_dir: str
    fixtures_example_outputs_dir: str


class FixtureValidateEntry(BaseModel):
    name: str
    stage: str


class FixturesConfig(BaseModel):
    files: list[FixtureValidateEntry]


class Config(BaseModel):
    app: AppConfig
    cors: CorsConfig
    llm: LlmConfig
    input_safety: InputSafetyConfig
    embedding: EmbeddingConfig
    onet: OnetConfig
    onet_matching: OnetMatchingConfig
    job_discovery: JobDiscoveryConfig
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
