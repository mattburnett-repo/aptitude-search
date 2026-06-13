"""Pipeline progress: log to console and optionally notify a callback (UI stream)."""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]


def emit_progress(message: str, *, on_progress: ProgressCallback | None = None) -> None:
    logger.info(message)
    if on_progress is not None:
        on_progress(message)
