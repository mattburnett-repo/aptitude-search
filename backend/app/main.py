from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import config
from app.core.models import PipelineRequest, Stage1Request, Stage2Request
from app.pipeline import run_pipeline, run_stage1, run_stage2

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
SmolagentsInstrumentor().instrument()

app = FastAPI(
    title=config.app.title,
    version=config.app.version,
    openapi_tags=[
        {"name": "Health", "Health check": "Liveness checks"},
        {"name": "Pipeline", "Full pipeline": "Full resume → aptitude → job search run"},
        {"name": "Pipeline Stages", "Stages for pipeline": "Individual pipeline stages (1 and 2)"},
    ],
)

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


@app.get("/health", tags=["Health"])
def health():
    return {"ok": True, "service": config.app.service}


@app.post("/v1/pipeline", tags=["Pipeline"])
def pipeline(body: PipelineRequest):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    return run_pipeline(body.resume, body.constraints)


@app.post("/v1/stages/1", tags=["Pipeline Stages"])
def stage1(body: Stage1Request):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    return {"aptitude_profile": run_stage1(body.resume)}


@app.post("/v1/stages/2", tags=["Pipeline Stages"])
def stage2(body: Stage2Request):
    return {
        "verified_matches": run_stage2(
            body.aptitude_profile, body.constraints
        )
    }
