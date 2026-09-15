"""Deterministic agreement and conflict logic for final A/B annotations."""

from __future__ import annotations

from dataclasses import dataclass

from .retry import ensure_same_final_evidence
from .schema import AnnotationResponse


@dataclass(frozen=True)
class AgreementDecision:
    calibration_item_id: str
    status: str
    reason: str


def same_final_evidence(
    annotation_a: AnnotationResponse,
    annotation_b: AnnotationResponse,
) -> bool:
    try:
        ensure_same_final_evidence(annotation_a, annotation_b)
    except ValueError:
        return False
    return True


def classify_annotation_pair(
    annotation_a: AnnotationResponse,
    annotation_b: AnnotationResponse,
) -> AgreementDecision:
    """Classify only final, non-superseded A/B rows."""

    if annotation_a.calibration_item_id != annotation_b.calibration_item_id:
        raise ValueError("A/B annotations must refer to the same calibration_item_id")
    if annotation_a.superseded or annotation_b.superseded:
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            "superseded first-pass annotation cannot enter final agreement",
        )
    if annotation_a.requires_evidence_retry or annotation_b.requires_evidence_retry:
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            "Evidence retry remains required before final agreement",
        )
    if not same_final_evidence(annotation_a, annotation_b):
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            "A/B final Evidence contract is not identical",
        )
    if annotation_a.primary_domain != annotation_b.primary_domain:
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            "primary_domain disagreement",
        )
    if annotation_a.taxonomy_fit != annotation_b.taxonomy_fit:
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            "taxonomy_fit disagreement",
        )
    if annotation_a.taxonomy_fit == "cross_domain" and set(
        annotation_a.secondary_domains
    ) != set(annotation_b.secondary_domains):
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            "cross_domain secondary_domains disagreement",
        )
    if annotation_a.taxonomy_fit in {
        "ambiguous",
        "taxonomy_gap",
        "out_of_scope",
        "insufficient_evidence",
    }:
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            f"taxonomy_fit={annotation_a.taxonomy_fit} requires review",
        )
    if annotation_a.confidence == "low" or annotation_b.confidence == "low":
        return AgreementDecision(
            annotation_a.calibration_item_id,
            "conflict",
            "low confidence requires review",
        )
    return AgreementDecision(
        annotation_a.calibration_item_id,
        "provisionally_agreed",
        "A/B meet the provisional agreement rules",
    )
