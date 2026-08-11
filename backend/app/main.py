from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_setup import configure_logging
from app.core.models import PipelineRequest, Stage1Request, Stage2Request, Stage3Request
from app.core.observability import init_observability
from app.core.request_context import RequestContextMiddleware
from app.core.resume_io import ingest_resume, prepare_pipeline_inputs
from app.core.stream_pipeline import stream_pipeline_response
from app.pipeline import run_pipeline, run_stage1, run_stage2, run_stage3
from app.onet.match import matches_to_json

configure_logging()
init_observability()

app = FastAPI(
    title=config.app.title,
    version=config.app.version,
    openapi_tags=[
        {"name": "Health", "description": "Liveness checks"},
        {"name": "Pipeline", "description": "Full resume → aptitude → job search run"},
        {
            "name": "Pipeline Stages",
            "description": "Individual pipeline stages (1, 2, and 3)",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
)
app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)

@app.get("/health", tags=["Health"])
def health():
    return {
        "ok": True,
        "service": config.app.service,
        "version": config.app.version,
    }


@app.post("/v1/pipeline", tags=["Pipeline"])
async def pipeline(body: PipelineRequest, stream: bool = False):
    """Run Stages 1→2→3: resume → aptitude profile → role family plan → job search."""
    if stream:
        return await stream_pipeline_response(body)
    resume, constraints = prepare_pipeline_inputs(body)
    return run_pipeline(resume, constraints)


@app.post("/v1/stages/1", tags=["Pipeline Stages"])
def stage1(body: Stage1Request):
    """Stage 1: sanitize resume text and extract a schema-strict aptitude profile."""
    return {"aptitude_profile": run_stage1(ingest_resume(body.resume))}


@app.post("/v1/stages/2", tags=["Pipeline Stages"])
def stage2(body: Stage2Request):
    """Stage 2: map aptitude profile to a role family plan (plus O*NET matches)."""
    result = run_stage2(body.aptitude_profile)
    return {
        "role_family_plan": result.role_family_plan,
        "occupation_matches": matches_to_json(list(result.occupation_matches)),
    }


@app.post("/v1/stages/3", tags=["Pipeline Stages"])
def stage3(body: Stage3Request):
    """Stage 3: discover, rank, and synthesize verified job matches from the profile."""
    return {
        "verified_matches": run_stage3(
            body.aptitude_profile,
            body.constraints,
            role_family_plan=body.role_family_plan,
        )
    }
