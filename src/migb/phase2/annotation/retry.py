"""Item-level Evidence retry decisions for the adaptive Gate 2C contract."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import AnnotationResponse


MAX_EVIDENCE_RETRY_COUNT = 1
RETRY_EVIDENCE_USABILITY = frozenset({"unreadable", "insufficient"})


@dataclass(frozen=True)
class RetryDecision:
    calibration_item_id: str
    required: bool
    triggered_by_a: bool
    triggered_by_b: bool
    reasons: tuple[str, ...]


def annotation_requires_evidence_retry(annotation: AnnotationResponse) -> bool:
    """Return whether one annotation output requests item-level Evidence retry."""

    return annotation.requires_evidence_retry


def decide_item_retry(
    annotation_a: AnnotationResponse,
    annotation_b: AnnotationResponse,
) -> RetryDecision:
    """Combine A/B outputs into one retry decision for the Item."""

    if annotation_a.calibration_item_id != annotation_b.calibration_item_id:
        raise ValueError("A/B annotations must refer to the same calibration_item_id")
    a_reasons: list[str] = []
    b_reasons: list[str] = []
    if annotation_a.evidence_usability in RETRY_EVIDENCE_USABILITY:
        a_reasons.append(f"a.evidence_usability={annotation_a.evidence_usability}")
    if annotation_a.taxonomy_fit == "insufficient_evidence":
        a_reasons.append("a.taxonomy_fit=insufficient_evidence")
    if annotation_b.evidence_usability in RETRY_EVIDENCE_USABILITY:
        b_reasons.append(f"b.evidence_usability={annotation_b.evidence_usability}")
    if annotation_b.taxonomy_fit == "insufficient_evidence":
        b_reasons.append("b.taxonomy_fit=insufficient_evidence")
    return RetryDecision(
        calibration_item_id=annotation_a.calibration_item_id,
        required=bool(a_reasons or b_reasons),
        triggered_by_a=bool(a_reasons),
        triggered_by_b=bool(b_reasons),
        reasons=tuple(a_reasons + b_reasons),
    )


def can_retry(current_retry_count: int) -> bool:
    if (
        isinstance(current_retry_count, bool)
        or not isinstance(current_retry_count, int)
        or current_retry_count < 0
    ):
        raise ValueError("current_retry_count must be a non-negative integer")
    return current_retry_count < MAX_EVIDENCE_RETRY_COUNT


def mark_first_pass_superseded(
    annotation_a: AnnotationResponse,
    annotation_b: AnnotationResponse,
) -> tuple[AnnotationResponse, AnnotationResponse]:
    """Mark both first-pass rows superseded when either side requested retry."""

    decision = decide_item_retry(annotation_a, annotation_b)
    if not decision.required:
        raise ValueError("first-pass annotations are not eligible for supersede without retry")
    return annotation_a.with_superseded(), annotation_b.with_superseded()


def ensure_same_final_evidence(
    annotation_a: AnnotationResponse,
    annotation_b: AnnotationResponse,
) -> None:
    """Raise if final A/B rows do not share every contract revision."""

    if annotation_a.calibration_item_id != annotation_b.calibration_item_id:
        raise ValueError("A/B annotations must refer to the same calibration_item_id")
    fields = (
        "evidence_revision",
        "taxonomy_revision",
        "prompt_revision",
        "schema_revision",
    )
    mismatches = [
        field
        for field in fields
        if getattr(annotation_a, field) != getattr(annotation_b, field)
    ]
    if mismatches:
        raise ValueError("A/B final Evidence contract mismatch: " + ", ".join(mismatches))
    if annotation_a.peer_annotation_visible or annotation_b.peer_annotation_visible:
        raise ValueError("peer annotation output must never be visible")
