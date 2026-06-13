"""Per-request id for logs and error responses."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import override
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def get_request_id() -> str:
    return request_id_var.get()


def error_response_headers(request: Request) -> dict[str, str]:
    request_id = getattr(request.state, "request_id", "") or get_request_id()
    if not request_id:
        return {}
    return {"X-Request-ID": request_id}


class RequestContextMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        logger = logging.getLogger(__name__)
        try:
            if request.url.path.startswith("/v1/"):
                logger.info(
                    "%s %s stream=%s",
                    request.method,
                    request.url.path,
                    request.query_params.get("stream", "0"),
                )
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
