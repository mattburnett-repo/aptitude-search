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
    api_key: str
    default_model: str
    temperature: float
    json_response_type: str

    @field_validator("api_key")
    @classmethod
    def api_key_must_be_set(cls, value: str) -> str:
        key = value.strip()
        if not key:
            raise ValueError("llm.api_key must be set in config.toml")
        return key


class PromptsConfig(BaseModel):
    stage1_file: str
    stage2_file: str


class SchemasConfig(BaseModel):
    constraints: str
    aptitude_profile: str


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
