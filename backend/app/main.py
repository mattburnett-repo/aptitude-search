from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import PipelineRequest, Stage1Request, Stage2Request
from app.pipeline import run_pipeline, run_stage1, run_stage2

app = FastAPI(title="aptitude-search-api", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_api_key(x_openai_api_key: str | None) -> str:
    if not x_openai_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-OpenAI-Api-Key header (BYO API key)",
        )
    return x_openai_api_key


@app.get("/health")
def health():
    return {"ok": True, "service": "aptitude-search-api"}


@app.post("/v1/pipeline")
def pipeline(
    body: PipelineRequest,
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    key = require_api_key(x_openai_api_key)
    try:
        return run_pipeline(key, body.resume, body.constraints, x_openai_model)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/stages/1")
def stage1(
    body: Stage1Request,
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    key = require_api_key(x_openai_api_key)
    try:
        return {"aptitude_profile": run_stage1(key, body.resume, x_openai_model)}
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/stages/2")
def stage2(
    body: Stage2Request,
    x_openai_api_key: str | None = Header(default=None),
    x_openai_model: str | None = Header(default=None),
):
    key = require_api_key(x_openai_api_key)
    try:
        return {
            "verified_matches": run_stage2(
                key, body.aptitude_profile, body.constraints, x_openai_model
            )
        }
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
