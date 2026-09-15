"""Gate 2C artifact names, identities, and offline row contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import AnnotationAttempt, AnnotationResponse


GATE2C_ARTIFACT_NAMES = (
    "annotation_attempts.jsonl",
    "annotation_final.parquet",
    "evidence_retries.parquet",
    "taxonomy_agreements.parquet",
    "taxonomy_conflicts.parquet",
    "manifest.json",
    "statistics.json",
)


def gate2c_artifact_paths(root: str | Path, gate2c_run_id: str) -> dict[str, Path]:
    """Return paths without creating directories or touching Runtime Artifacts."""

    if not gate2c_run_id or "/" in gate2c_run_id or "\\" in gate2c_run_id:
        raise ValueError("gate2c_run_id must be a non-empty directory-safe identifier")
    run_directory = Path(root) / "phase2" / "runs" / gate2c_run_id
    return {name: run_directory / name for name in GATE2C_ARTIFACT_NAMES}


def artifact_row_identity(row: dict[str, Any]) -> tuple[str, ...]:
    """Return the stable identity used to detect row mix-ups."""

    required = (
        "gate2c_run_id",
        "calibration_sample_id",
        "calibration_item_id",
        "annotator_id",
        "annotation_pass",
        "attempt_id",
    )
    missing = [field for field in required if not row.get(field)]
    if missing:
        raise ValueError(f"artifact row identity missing fields: {missing}")
    return tuple(str(row[field]) for field in required)


def annotation_attempt_row(
    attempt: AnnotationAttempt,
    *,
    gate2c_run_id: str,
) -> dict[str, Any]:
    """Build one JSONL attempt row, including failed parse attempts."""

    row = attempt.to_dict()
    row.update(
        {
            "gate2c_run_id": gate2c_run_id,
            "annotation_record_id": f"{gate2c_run_id}:{attempt.request.calibration_item_id}:{attempt.attempt_id}",
            "calibration_sample_id": attempt.request.calibration_sample_id,
            "calibration_item_id": attempt.request.calibration_item_id,
            "relative_path": attempt.request.relative_path,
            "evidence_revision": attempt.request.evidence_revision,
            "taxonomy_revision": attempt.request.taxonomy_revision,
            "prompt_revision": attempt.request.prompt_revision,
            "schema_revision": attempt.request.schema_revision,
        }
    )
    return row


def final_annotation_row(
    response: AnnotationResponse,
    *,
    gate2c_run_id: str,
    attempt_id: str,
    first_pass_artifact_ref: str | None = None,
) -> dict[str, Any]:
    """Build a final row and reject superseded first-pass results."""

    if response.superseded:
        raise ValueError("superseded annotation cannot be written as final")
    row = response.to_dict()
    row.update(
        {
            "gate2c_run_id": gate2c_run_id,
            "annotation_record_id": response.annotation_record_id
            or f"{gate2c_run_id}:{response.calibration_item_id}:{response.annotator_id}",
            "attempt_id": attempt_id,
            "first_pass_artifact_ref": first_pass_artifact_ref,
        }
    )
    return row


def evidence_retry_row(
    *,
    gate2c_run_id: str,
    calibration_sample_id: str,
    decision: Any,
    source_evidence_revision: str,
    final_evidence_revision: str,
    ocr_engine: str,
    ocr_version: str,
    render_dpi: int,
    retry_status: str,
    final_evidence_char_count: int | None,
    created_at: str,
) -> dict[str, Any]:
    """Build one item-level Evidence retry row without storing raw Evidence text."""

    return {
        "gate2c_run_id": gate2c_run_id,
        "calibration_sample_id": calibration_sample_id,
        "calibration_item_id": decision.calibration_item_id,
        "retry_triggered_by_a": decision.triggered_by_a,
        "retry_triggered_by_b": decision.triggered_by_b,
        "retry_reason": list(decision.reasons),
        "source_evidence_revision": source_evidence_revision,
        "final_evidence_revision": final_evidence_revision,
        "ocr_engine": ocr_engine,
        "ocr_version": ocr_version,
        "render_dpi": render_dpi,
        "retry_status": retry_status,
        "final_evidence_char_count": final_evidence_char_count,
        "created_at": created_at,
    }
