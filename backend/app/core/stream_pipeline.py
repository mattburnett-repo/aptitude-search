"""NDJSON streaming wrapper for POST /v1/pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Literal, TypedDict

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.core.models import PipelineRequest
from app.core.request_context import get_request_id
from app.core.resume_io import parse_pipeline_body
from app.pipeline import run_pipeline

logger = logging.getLogger(__name__)


class ProgressEvent(TypedDict):
    type: Literal["progress"]
    message: str


class ResultEvent(TypedDict):
    type: Literal["result"]
    data: dict[str, object]


class ErrorEvent(TypedDict):
    type: Literal["error"]
    detail: str
    request_id: str


StreamEvent = ProgressEvent | ResultEvent | ErrorEvent


async def stream_pipeline_response(body: PipelineRequest) -> StreamingResponse:
    queue: asyncio.Queue[StreamEvent] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def put_event(event: StreamEvent) -> None:
        queue.put_nowait(event)

    def on_progress(message: str) -> None:
        _ = loop.call_soon_threadsafe(
            put_event,
            ProgressEvent(type="progress", message=message),
        )

    def run_sync() -> None:
        try:
            resume, constraints = parse_pipeline_body(body, on_progress=on_progress)
            if not resume.strip():
                raise ValueError("resume is required")
            result = run_pipeline(resume, constraints, on_progress=on_progress)
            _ = loop.call_soon_threadsafe(
                put_event,
                ResultEvent(type="result", data=result),
            )
        except HTTPException as exc:
            logger.warning("HTTP %s: %s", exc.status_code, exc.detail)
            _ = loop.call_soon_threadsafe(
                put_event,
                ErrorEvent(
                    type="error",
                    detail=str(exc.detail),
                    request_id=get_request_id(),
                ),
            )
        except Exception as exc:
            logger.exception("Stream pipeline failed")
            _ = loop.call_soon_threadsafe(
                put_event,
                ErrorEvent(
                    type="error",
                    detail=str(exc),
                    request_id=get_request_id(),
                ),
            )

    _ = asyncio.create_task(asyncio.to_thread(run_sync))

    async def generate():
        while True:
            event = await queue.get()
            yield json.dumps(event) + "\n"
            if event["type"] in ("result", "error"):
                break

    return StreamingResponse(generate(), media_type="application/x-ndjson")
