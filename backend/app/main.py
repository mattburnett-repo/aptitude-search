from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


async def pipeline_exception_handler(
    _request: Request, exc: ValueError | RuntimeError
) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


app.add_exception_handler(ValueError, pipeline_exception_handler)
app.add_exception_handler(RuntimeError, pipeline_exception_handler)


@app.get("/health")
def health():
    return {"ok": True, "service": config.app.service}


@app.post("/v1/pipeline")
def pipeline(body: PipelineRequest):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    return run_pipeline(body.resume, body.constraints)


@app.post("/v1/stages/1")
def stage1(body: Stage1Request):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    return {"aptitude_profile": run_stage1(body.resume)}


@app.post("/v1/stages/2")
def stage2(body: Stage2Request):
    return {
        "verified_matches": run_stage2(
            body.aptitude_profile, body.constraints
        )
    }
