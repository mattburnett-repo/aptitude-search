"""Root logger setup for the API process."""

from __future__ import annotations

import logging
import sys

from app.core.request_context import RequestIdFilter


def configure_logging() -> None:
    """Configure stdout logging with per-request id on every record."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s request_id=%(request_id)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    request_id_filter = RequestIdFilter()
    for handler in logging.root.handlers:
        handler.addFilter(request_id_filter)
    logging.root.addFilter(request_id_filter)
