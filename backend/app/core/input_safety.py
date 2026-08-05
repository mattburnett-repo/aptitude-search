"""Resume ingress: prompt-injection gate and PII deletion before Stage 1."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import TYPE_CHECKING, cast

from fastapi import HTTPException

from app.core.config import config
from app.core.llm_input_guard import resume_chunk_malicious
from app.core.progress import ProgressCallback, emit_progress

if TYPE_CHECKING:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine

logger = logging.getLogger(__name__)

INPUT_REJECTED_MESSAGE = (
    "We couldn't process this resume. Check the file and try again, "
    "or paste plain text instead."
)

_INJECTION_REGEXES: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"<\s*/?\s*system\s*>",
        r"<\s*/?\s*assistant\s*>",
        r"<\s*/?\s*user\s*>",
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(previous\s+)?(instructions|rules|prompts)",
        r"forget\s+(all\s+)?(previous\s+)?(instructions|rules|context)",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"new\s+instructions\s*:",
        r"system\s+prompt\s*:",
        r"override\s+(the\s+)?(system|developer)\s+(prompt|instructions)",
    )
)

_INJECTION_PHRASES: tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard your instructions",
    "disregard all prior instructions",
    "forget your instructions",
    "you are now dan",
    "jailbreak",
    "developer mode enabled",
    "do anything now",
)

_CONTACT_HEADER_MARKERS = (
    "@",
    "github.com",
    "linkedin.com",
    "phone:",
    "tel:",
    "mailto:",
)

_PRESIDIO_LANGUAGE = "en"
_SPACY_MODEL = "en_core_web_sm"
_SPACY_LABELS_TO_IGNORE = (
    "CARDINAL",
    "PERCENT",
    "ORDINAL",
    "QUANTITY",
    "MONEY",
    "EVENT",
    "LANGUAGE",
    "LAW",
    "PRODUCT",
    "WORK_OF_ART",
)


def prepare_resume(
    text: str,
    *,
    on_progress: ProgressCallback | None = None,
) -> str:
    """Run injection checks on original text, then delete PII for downstream stages."""
    stripped = text.strip()
    if not stripped:
        return stripped
    if len(stripped) > config.input_safety.max_resume_chars:
        raise HTTPException(
            status_code=400,
            detail=f"Resume exceeds maximum length ({config.input_safety.max_resume_chars} characters).",
        )
    emit_progress("Checking resume safety…", on_progress=on_progress)
    _check_injection(stripped)
    emit_progress("Removing contact information…", on_progress=on_progress)
    return _delete_pii(stripped)


def _reject_injection(reason: str) -> None:
    logger.warning("input_safety injection blocked: %s", reason)
    raise HTTPException(status_code=400, detail=INPUT_REJECTED_MESSAGE)


def _check_injection(text: str) -> None:
    for pattern in _INJECTION_REGEXES:
        if pattern.search(text):
            _reject_injection("regex")
            return
    lowered = text.lower()
    for phrase in _INJECTION_PHRASES:
        if phrase in lowered:
            _reject_injection("blocklist")
            return
    if resume_chunk_malicious(text):
        _reject_injection("prompt_guard")


def _strip_contact_header_lines(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    kept: list[str] = []
    past_header = False
    for index, line in enumerate(lines):
        if past_header or index >= 8:
            kept.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            past_header = True
            continue
        lower = stripped.lower()
        if any(marker in lower for marker in _CONTACT_HEADER_MARKERS):
            continue
        if re.match(r"^[\w\s.'-]+\s*\|\s*[\w\s,.'-]+", stripped):
            continue
        past_header = True
        kept.append(line)
    return "\n".join(kept).strip() if kept else text


@lru_cache(maxsize=1)
def _presidio_engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_analyzer.predefined_recognizers import (
        EmailRecognizer,
        PhoneRecognizer,
        SpacyRecognizer,
        UsSsnRecognizer,
    )
    from presidio_anonymizer import AnonymizerEngine

    logging.getLogger("presidio-analyzer").setLevel(logging.WARNING)

    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": _PRESIDIO_LANGUAGE, "model_name": _SPACY_MODEL}],
            "ner_model_configuration": {
                "labels_to_ignore": list(_SPACY_LABELS_TO_IGNORE),
            },
        }
    ).create_engine()

    registry = RecognizerRegistry(supported_languages=[_PRESIDIO_LANGUAGE])
    for recognizer_cls in (
        EmailRecognizer,
        PhoneRecognizer,
        SpacyRecognizer,
        UsSsnRecognizer,
    ):
        registry.add_recognizer(recognizer_cls())

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=[_PRESIDIO_LANGUAGE],
    )
    return analyzer, AnonymizerEngine()


def _delete_pii(text: str) -> str:
    scrubbed = _strip_contact_header_lines(text)
    analyzer, anonymizer = _presidio_engines()
    from presidio_anonymizer.entities import OperatorConfig
    from presidio_anonymizer.entities.engine.recognizer_result import (
        RecognizerResult as AnonymizerRecognizerResult,
    )

    results = analyzer.analyze(
        text=scrubbed,
        entities=config.input_safety.pii_entities,
        language="en",
    )
    if not results:
        return _collapse_whitespace(scrubbed)
    operators = {
        entity: OperatorConfig("redact") for entity in config.input_safety.pii_entities
    }
    operators["DEFAULT"] = OperatorConfig("redact")
    anonymized = anonymizer.anonymize(
        text=scrubbed,
        analyzer_results=cast(list[AnonymizerRecognizerResult], results),
        operators=operators,
    )
    return _collapse_whitespace(anonymized.text)


def _collapse_whitespace(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    collapsed: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank and collapsed:
                collapsed.append("")
            blank = True
            continue
        blank = False
        collapsed.append(line)
    return "\n".join(collapsed).strip()
