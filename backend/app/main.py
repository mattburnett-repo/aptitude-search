from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.models import PipelineRequest, Stage1Request, Stage2Request
from app.pipeline import run_pipeline, run_stage1, run_stage2

app = FastAPI(title=config.app.title, version=config.app.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
)


@app.get("/health")
def health():
    return {"ok": True, "service": config.app.service}


@app.post("/v1/pipeline")
def pipeline(body: PipelineRequest):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    try:
        return run_pipeline(body.resume, body.constraints)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/stages/1")
def stage1(body: Stage1Request):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    try:
        return {"aptitude_profile": run_stage1(body.resume)}
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/stages/2")
def stage2(body: Stage2Request):
    try:
        return {
            "verified_matches": run_stage2(
                body.aptitude_profile, body.constraints
            )
        }
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
