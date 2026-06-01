import sys
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

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
    temperature: float

    @field_validator("aptitude_model_key")
    @classmethod
    def aptitude_model_key_must_be_set(cls, value: str) -> str:
        key = value.strip()
        if not key:
            raise ValueError("llm.aptitude_model_key must be set in config.toml")
        return key

    @field_validator("aptitude_model")
    @classmethod
    def aptitude_model_must_be_set(cls, value: str) -> str:
        model = value.strip()
        if not model:
            raise ValueError("llm.aptitude_model must be set in config.toml")
        return model


class PromptsConfig(BaseModel):
    stage1_file: str
    stage2_file: str


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
