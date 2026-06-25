import logging
import sys
from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.types import ExceptionHandler

from app.core.config import config
from app.core.models import PipelineRequest, Stage1Request, Stage2Request, Stage3Request
from app.core.request_context import (
    error_response_headers,
    RequestContextMiddleware,
    RequestIdFilter,
)
from app.core.resume_io import parse_pipeline_body
from app.core.stream_pipeline import stream_pipeline_response
from app.pipeline import run_pipeline, run_stage1, run_stage3
from app.role_family_plan import run_stage2

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s request_id=%(request_id)s %(name)s %(message)s",
    stream=sys.stdout,
)
_request_id_filter = RequestIdFilter()
for _handler in logging.root.handlers:
    _handler.addFilter(_request_id_filter)
logging.root.addFilter(_request_id_filter)
logger = logging.getLogger(__name__)

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
SmolagentsInstrumentor().instrument()

app = FastAPI(
    title=config.app.title,
    version=config.app.version,
    openapi_tags=[
        {"name": "Health", "Health check": "Liveness checks"},
        {"name": "Pipeline", "Full pipeline": "Full resume → aptitude → job search run"},
        {"name": "Pipeline Stages", "Stages for pipeline": "Individual pipeline stages (1, 2, and 3)"},
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


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    logger.warning("HTTP %s: %s", exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": _request_id(request)},
        headers=error_response_headers(request),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Request validation failed: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "request_id": _request_id(request)},
        headers=error_response_headers(request),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Request failed: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "request_id": _request_id(request)},
        headers=error_response_headers(request),
    )


app.add_exception_handler(HTTPException, cast(ExceptionHandler, http_exception_handler))
app.add_exception_handler(
    RequestValidationError, cast(ExceptionHandler, validation_exception_handler)
)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/health", tags=["Health"])
def health():
    return {"ok": True, "service": config.app.service}


@app.post("/v1/pipeline", tags=["Pipeline"])
async def pipeline(body: PipelineRequest, stream: bool = False):
    # resume may be pasted text or text extracted from resume_pdf_base64
    if not body.resume.strip() and not body.resume_pdf_base64:
        raise HTTPException(status_code=400, detail="resume is required")
    if stream:
        return await stream_pipeline_response(body)
    resume, constraints = parse_pipeline_body(body)
    return run_pipeline(resume, constraints)


@app.post("/v1/stages/1", tags=["Pipeline Stages"])
def stage1(body: Stage1Request):
    if not body.resume.strip():
        raise HTTPException(status_code=400, detail="resume is required")
    return {"aptitude_profile": run_stage1(body.resume)}


@app.post("/v1/stages/2", tags=["Pipeline Stages"])
def stage2(body: Stage2Request):
    return {"role_family_plan": run_stage2(body.aptitude_profile)}


@app.post("/v1/stages/3", tags=["Pipeline Stages"])
def stage3(body: Stage3Request):
    return {
        "verified_matches": run_stage3(
            body.aptitude_profile,
            body.constraints,
            role_family_plan=body.role_family_plan,
        )
    }
