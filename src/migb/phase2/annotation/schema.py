"""Strict, offline validation for the Gate 2C annotation contract."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Any, Mapping


class AnnotationSchemaError(ValueError):
    """Raised when a model output violates the canonical annotation schema."""


PRIMARY_DOMAIN_VALUES = tuple(f"D{index:02d}" for index in range(1, 13)) + (
    "OUT_OF_SCOPE",
    "UNCERTAIN",
)
TAXONOMY_FIT_VALUES = (
    "clear_fit",
    "cross_domain",
    "ambiguous",
    "taxonomy_gap",
    "out_of_scope",
    "insufficient_evidence",
)
CONFIDENCE_VALUES = ("high", "medium", "low")
EVIDENCE_USABILITY_VALUES = (
    "usable",
    "partially_usable",
    "unreadable",
    "insufficient",
)
REVIEW_STATUS_VALUES = (
    "annotated_a",
    "annotated_b",
    "provisionally_agreed",
    "conflict",
    "human_reviewed",
    "deferred",
)

MODEL_OUTPUT_FIELDS = (
    "primary_domain",
    "secondary_domains",
    "taxonomy_fit",
    "confidence",
    "evidence_usability",
    "evidence_keywords",
    "evidence_rationale",
    "review_note",
)
SCHEMA_REVISION = "taxonomy-annotation-schema-v0.1"


def schema_definition() -> dict[str, Any]:
    """Return the reviewed model-output JSON Schema definition."""

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_REVISION,
        "type": "object",
        "additionalProperties": False,
        "required": list(MODEL_OUTPUT_FIELDS),
        "properties": {
            "primary_domain": {
                "type": "string",
                "enum": list(PRIMARY_DOMAIN_VALUES),
            },
            "secondary_domains": {
                "type": "array",
                "minItems": 0,
                "maxItems": 3,
                "uniqueItems": True,
                "items": {"type": "string", "enum": list(PRIMARY_DOMAIN_VALUES[:12])},
            },
            "taxonomy_fit": {"type": "string", "enum": list(TAXONOMY_FIT_VALUES)},
            "confidence": {"type": "string", "enum": list(CONFIDENCE_VALUES)},
            "evidence_usability": {
                "type": "string",
                "enum": list(EVIDENCE_USABILITY_VALUES),
            },
            "evidence_keywords": {
                "type": "array",
                "minItems": 0,
                "maxItems": 8,
                "items": {"type": "string", "minLength": 1},
            },
            "evidence_rationale": {"type": "string", "minLength": 1},
            "review_note": {"type": ["string", "null"]},
        },
    }


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def annotation_schema_hash() -> str:
    """Return the stable hash of the canonical model-output schema."""

    return hashlib.sha256(_canonical_json_bytes(schema_definition())).hexdigest()


def _require_string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise AnnotationSchemaError(f"{field} must be a non-empty string")
    return value


def _require_enum(value: Any, field: str, allowed: tuple[str, ...]) -> str:
    value = _require_string(value, field)
    if value not in allowed:
        raise AnnotationSchemaError(f"{field} must be one of {allowed}; got {value!r}")
    return value


def _sentence_count(value: str) -> int:
    chunks = [chunk.strip() for chunk in re.split(r"[。！？!?；;.!]+", value) if chunk.strip()]
    return max(1, len(chunks))


def validate_model_output(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one strict provider model-output object.

    The function intentionally rejects unknown fields.  Derived routing fields,
    identity, provider metadata, and supersede state are attached after this
    validation and are not model-controlled.
    """

    if not isinstance(payload, Mapping):
        raise AnnotationSchemaError("model output must be a JSON object")
    actual_fields = set(payload)
    expected_fields = set(MODEL_OUTPUT_FIELDS)
    unknown = sorted(actual_fields - expected_fields)
    missing = sorted(expected_fields - actual_fields)
    if unknown:
        raise AnnotationSchemaError(f"unknown annotation fields: {unknown}")
    if missing:
        raise AnnotationSchemaError(f"missing annotation fields: {missing}")

    primary_domain = _require_enum(payload["primary_domain"], "primary_domain", PRIMARY_DOMAIN_VALUES)
    secondary_raw = payload["secondary_domains"]
    if not isinstance(secondary_raw, list):
        raise AnnotationSchemaError("secondary_domains must be a JSON array")
    if len(secondary_raw) > 3:
        raise AnnotationSchemaError("secondary_domains must contain at most 3 values")
    secondary_domains = [
        _require_enum(value, "secondary_domains[]", PRIMARY_DOMAIN_VALUES[:12])
        for value in secondary_raw
    ]
    if len(set(secondary_domains)) != len(secondary_domains):
        raise AnnotationSchemaError("secondary_domains must not contain duplicates")
    if primary_domain in secondary_domains:
        raise AnnotationSchemaError("secondary_domains cannot contain primary_domain")

    taxonomy_fit = _require_enum(payload["taxonomy_fit"], "taxonomy_fit", TAXONOMY_FIT_VALUES)
    confidence = _require_enum(payload["confidence"], "confidence", CONFIDENCE_VALUES)
    evidence_usability = _require_enum(
        payload["evidence_usability"],
        "evidence_usability",
        EVIDENCE_USABILITY_VALUES,
    )

    keywords_raw = payload["evidence_keywords"]
    if not isinstance(keywords_raw, list):
        raise AnnotationSchemaError("evidence_keywords must be a JSON array")
    if len(keywords_raw) > 8:
        raise AnnotationSchemaError("evidence_keywords must contain at most 8 values")
    evidence_keywords = [
        _require_string(value, "evidence_keywords[]") for value in keywords_raw
    ]
    if len(set(evidence_keywords)) != len(evidence_keywords):
        raise AnnotationSchemaError("evidence_keywords must not contain duplicates")

    rationale = _require_string(payload["evidence_rationale"], "evidence_rationale")
    if _sentence_count(rationale) > 3:
        raise AnnotationSchemaError("evidence_rationale must contain at most 3 concise sentences")
    review_note = payload["review_note"]
    if review_note is not None:
        review_note = _require_string(review_note, "review_note")

    return {
        "primary_domain": primary_domain,
        "secondary_domains": secondary_domains,
        "taxonomy_fit": taxonomy_fit,
        "confidence": confidence,
        "evidence_usability": evidence_usability,
        "evidence_keywords": evidence_keywords,
        "evidence_rationale": rationale,
        "review_note": review_note,
    }


@dataclass(frozen=True)
class AnnotationRequest:
    """The only document information that may enter an Annotator request."""

    calibration_sample_id: str
    calibration_item_id: str
    evidence_revision: str
    taxonomy_revision: str
    prompt_revision: str
    schema_revision: str
    evidence: str
    filename_title: str | None = None
    metadata_title: str | None = None
    page_count: int | None = None
    relative_path: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "calibration_sample_id",
            "calibration_item_id",
            "evidence_revision",
            "taxonomy_revision",
            "prompt_revision",
            "schema_revision",
        ):
            _require_string(getattr(self, field), field)
        if not isinstance(self.evidence, str):
            raise AnnotationSchemaError("evidence must be a string")
        if self.filename_title is not None:
            _require_string(self.filename_title, "filename_title")
        if self.metadata_title is not None:
            _require_string(self.metadata_title, "metadata_title")
        if self.relative_path is not None:
            _require_string(self.relative_path, "relative_path")
        if self.page_count is not None and (
            isinstance(self.page_count, bool)
            or not isinstance(self.page_count, int)
            or self.page_count < 0
        ):
            raise AnnotationSchemaError("page_count must be a non-negative integer or null")

    def permitted_metadata(self) -> dict[str, Any]:
        """Return metadata explicitly allowed in the prompt."""

        return {
            key: value
            for key, value in {
                "filename_title": self.filename_title,
                "metadata_title": self.metadata_title,
                "page_count": self.page_count,
            }.items()
            if value is not None
        }


@dataclass(frozen=True)
class AnnotationResponse:
    """A validated canonical annotation enriched with execution provenance."""

    calibration_sample_id: str
    calibration_item_id: str
    annotator_id: str
    annotation_pass: str
    taxonomy_revision: str
    prompt_revision: str
    schema_revision: str
    evidence_revision: str
    primary_domain: str
    secondary_domains: tuple[str, ...]
    taxonomy_fit: str
    confidence: str
    evidence_usability: str
    evidence_keywords: tuple[str, ...]
    evidence_rationale: str
    review_note: str | None
    review_status: str
    relative_path: str | None = None
    gate2c_run_id: str | None = None
    annotation_record_id: str | None = None
    provider: str | None = None
    requested_model: str | None = None
    resolved_model: str | None = None
    model_version_if_available: str | None = None
    request_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens_if_available: int | None = None
    latency_ms: int | None = None
    prompt_hash: str | None = None
    taxonomy_payload_hash: str | None = None
    schema_hash: str | None = None
    peer_annotation_visible: bool = False
    superseded: bool = False
    superseded_reason: str | None = None

    def __post_init__(self) -> None:
        _require_string(self.calibration_sample_id, "calibration_sample_id")
        _require_string(self.calibration_item_id, "calibration_item_id")
        _require_string(self.annotator_id, "annotator_id")
        _require_string(self.annotation_pass, "annotation_pass")
        if self.relative_path is not None:
            _require_string(self.relative_path, "relative_path")
        for field in ("gate2c_run_id", "annotation_record_id"):
            value = getattr(self, field)
            if value is not None:
                _require_string(value, field)
        for field in (
            "taxonomy_revision",
            "prompt_revision",
            "schema_revision",
            "evidence_revision",
        ):
            _require_string(getattr(self, field), field)
        output = validate_model_output(
            {
                "primary_domain": self.primary_domain,
                "secondary_domains": list(self.secondary_domains),
                "taxonomy_fit": self.taxonomy_fit,
                "confidence": self.confidence,
                "evidence_usability": self.evidence_usability,
                "evidence_keywords": list(self.evidence_keywords),
                "evidence_rationale": self.evidence_rationale,
                "review_note": self.review_note,
            }
        )
        if self.review_status not in REVIEW_STATUS_VALUES:
            raise AnnotationSchemaError(
                f"review_status must be one of {REVIEW_STATUS_VALUES}; got {self.review_status!r}"
            )
        if self.peer_annotation_visible:
            raise AnnotationSchemaError("peer_annotation_visible must remain false")
        for field in ("input_tokens", "output_tokens", "reasoning_tokens_if_available", "latency_ms"):
            value = getattr(self, field)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise AnnotationSchemaError(f"{field} must be a non-negative integer or null")
        if self.superseded and self.superseded_reason != "evidence_retry":
            raise AnnotationSchemaError(
                "superseded annotations must use superseded_reason=evidence_retry"
            )
        if not self.superseded and self.superseded_reason is not None:
            raise AnnotationSchemaError("non-superseded annotations cannot have superseded_reason")
        object.__setattr__(self, "secondary_domains", tuple(output["secondary_domains"]))
        object.__setattr__(self, "evidence_keywords", tuple(output["evidence_keywords"]))

    @property
    def requires_evidence_retry(self) -> bool:
        return self.evidence_usability in {"unreadable", "insufficient"} or (
            self.taxonomy_fit == "insufficient_evidence"
        )

    def with_superseded(self) -> "AnnotationResponse":
        return replace(self, superseded=True, superseded_reason="evidence_retry")

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate2c_run_id": self.gate2c_run_id,
            "annotation_record_id": self.annotation_record_id,
            "calibration_sample_id": self.calibration_sample_id,
            "calibration_item_id": self.calibration_item_id,
            "annotator_id": self.annotator_id,
            "annotation_pass": self.annotation_pass,
            "taxonomy_revision": self.taxonomy_revision,
            "prompt_revision": self.prompt_revision,
            "schema_revision": self.schema_revision,
            "evidence_revision": self.evidence_revision,
            "primary_domain": self.primary_domain,
            "secondary_domains": list(self.secondary_domains),
            "taxonomy_fit": self.taxonomy_fit,
            "confidence": self.confidence,
            "evidence_usability": self.evidence_usability,
            "requires_evidence_retry": self.requires_evidence_retry,
            "evidence_keywords": list(self.evidence_keywords),
            "evidence_rationale": self.evidence_rationale,
            "review_note": self.review_note,
            "review_status": self.review_status,
            "relative_path": self.relative_path,
            "provider": self.provider,
            "requested_model": self.requested_model,
            "resolved_model": self.resolved_model,
            "model_version_if_available": self.model_version_if_available,
            "request_id": self.request_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens_if_available": self.reasoning_tokens_if_available,
            "latency_ms": self.latency_ms,
            "prompt_hash": self.prompt_hash,
            "taxonomy_payload_hash": self.taxonomy_payload_hash,
            "schema_hash": self.schema_hash,
            "peer_annotation_visible": self.peer_annotation_visible,
            "superseded": self.superseded,
            "superseded_reason": self.superseded_reason,
        }


@dataclass(frozen=True)
class AnnotationAttempt:
    """One actual model or format attempt, including parse failure state."""

    attempt_id: str
    request: AnnotationRequest
    annotator_id: str
    annotation_pass: str
    parse_status: str
    response: AnnotationResponse | None = None
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        _require_string(self.attempt_id, "attempt_id")
        _require_string(self.annotator_id, "annotator_id")
        _require_string(self.annotation_pass, "annotation_pass")
        if self.parse_status not in {"passed", "failed"}:
            raise AnnotationSchemaError("parse_status must be passed or failed")
        if self.parse_status == "passed" and self.response is None:
            raise AnnotationSchemaError("passed attempts require a parsed response")
        if self.parse_status == "failed" and self.response is not None:
            raise AnnotationSchemaError("failed attempts cannot contain a parsed response")
        if self.parse_status == "failed" and not self.error_message:
            raise AnnotationSchemaError("failed attempts require an error_message")

    def to_dict(self) -> dict[str, Any]:
        result = {
            "attempt_id": self.attempt_id,
            "annotator_id": self.annotator_id,
            "annotation_pass": self.annotation_pass,
            "parse_status": self.parse_status,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }
        result.update(self.response.to_dict() if self.response is not None else {})
        return result
