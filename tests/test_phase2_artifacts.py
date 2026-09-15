from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from migb.phase2.artifacts import (
    EVIDENCE_JSONL_FIELDS,
    PHASE2_ARTIFACT_NAMES,
    calibration_sample_schema,
    validate_phase2_artifacts,
    write_phase2_artifacts,
)


def _sample_row(item_id: str) -> dict[str, object]:
    return {
        "phase2_run_id": "p2b-test",
        "calibration_sample_id": "sample-test",
        "calibration_item_id": item_id,
        "sample_role": "main",
        "pool_name": "main",
        "file_instance_id": f"file-{item_id}",
        "sha256": "sha",
        "source_root_id": "root",
        "relative_path": f"group/{item_id}.pdf",
        "parent_group": "group",
        "file_name": f"{item_id}.pdf",
        "size_bytes": 10,
        "mtime_ns": 20,
        "inventory_status": "success",
        "pdf_open_status": "success",
        "pdf_status": "valid",
        "page_count": 1,
        "text_layer_status": "text_present",
        "filename_parse_status": "matched",
        "exact_duplicate_group_id": None,
        "exact_duplicate_representative": True,
        "group_population": 1,
        "group_quota": 1,
        "selection_rank_or_index": 0,
        "sampling_method": "test",
        "full_inventory_run_id": "full-test",
        "inventory_schema_version": "inventory-v0.2",
    }


def _evidence_row(item_id: str) -> dict[str, object]:
    row = {field: None for field in EVIDENCE_JSONL_FIELDS}
    row.update(
        {
            "phase2_run_id": "p2b-test",
            "calibration_sample_id": "sample-test",
            "calibration_item_id": item_id,
            "file_instance_id": f"file-{item_id}",
            "pool_name": "main",
            "relative_path": f"group/{item_id}.pdf",
            "parent_group": "group",
            "evidence_page_indices": [0],
            "evidence_char_count": 3,
            "raw_text_char_count": 3,
            "evidence_truncated": False,
            "evidence_status": "success",
            "source_changed_during_evidence": False,
            "evidence_revision": "evidence-v0.1-gate2b",
        }
    )
    return row


def test_phase2_artifacts_have_explicit_schema_and_checksum_validation(tmp_path: Path) -> None:
    sample_rows = [_sample_row("one"), _sample_row("two")]
    evidence_rows = [_evidence_row("one"), _evidence_row("two")]
    manifest = {"phase2_run_id": "p2b-test", "stage": "gate2b", "run_status": "completed"}
    statistics = {"sample_row_count": 2, "evidence_row_count": 2}
    write_phase2_artifacts(tmp_path, sample_rows, evidence_rows, manifest, statistics)

    table = pq.read_table(tmp_path / "calibration_sample.parquet")
    assert table.schema.equals(calibration_sample_schema())
    assert validate_phase2_artifacts(tmp_path, expected_sample_count=2)["status"] == "passed"
    assert set(path.name for path in tmp_path.iterdir()) == set(PHASE2_ARTIFACT_NAMES)
    saved_manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert {item["path"] for item in saved_manifest["output_artifacts"]} == set(
        PHASE2_ARTIFACT_NAMES
    )


def test_phase2_artifact_validation_rejects_evidence_reordering(tmp_path: Path) -> None:
    sample_rows = [_sample_row("one"), _sample_row("two")]
    evidence_rows = [_evidence_row("two"), _evidence_row("one")]
    write_phase2_artifacts(
        tmp_path,
        sample_rows,
        evidence_rows,
        {"phase2_run_id": "p2b-test"},
        {"sample_row_count": 2},
    )
    try:
        validate_phase2_artifacts(tmp_path)
    except ValueError as exc:
        assert "order" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("reordered Evidence must fail validation")
