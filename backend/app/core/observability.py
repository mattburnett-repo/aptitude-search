"""Sentry and OpenTelemetry setup for the API process."""

from __future__ import annotations

import os

import sentry_sdk
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_observability() -> None:
    """Initialize Sentry (if DSN set) and the OTLP tracer provider."""
    sentry_dsn = os.environ.get("SENTRY_DSN", "").strip()
    if sentry_dsn:
        _ = sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
            traces_sample_rate=0.0,
            send_default_pii=False,
        )

    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
