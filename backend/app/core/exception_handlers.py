"""FastAPI exception handlers for JSON error responses with request_id."""

from __future__ import annotations

import logging
from typing import cast

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from app.core.request_context import error_response_headers

logger = logging.getLogger(__name__)


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
    _ = sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "request_id": _request_id(request)},
        headers=error_response_headers(request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        HTTPException, cast(ExceptionHandler, http_exception_handler)
    )
    app.add_exception_handler(
        RequestValidationError, cast(ExceptionHandler, validation_exception_handler)
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
