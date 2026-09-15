"""Explicit Phase 2 artifact schemas, writers, and validators."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from migb.inventory.artifacts import (
    artifact_descriptor,
    json_bytes,
    sha256_path,
    write_json_atomic,
    write_parquet_atomic,
)


PHASE2_ARTIFACT_NAMES = (
    "calibration_sample.parquet",
    "calibration_evidence.jsonl",
    "manifest.json",
    "statistics.json",
)
PHASE2_SCHEMA_VERSION = "phase2-calibration-v0.1"
EVIDENCE_JSONL_FIELDS = (
    "phase2_run_id",
    "calibration_sample_id",
    "calibration_item_id",
    "file_instance_id",
    "pool_name",
    "relative_path",
    "parent_group",
    "sha256",
    "page_count",
    "text_layer_status",
    "filename_title",
    "metadata_title",
    "evidence_text",
    "evidence_page_indices",
    "evidence_char_count",
    "raw_text_char_count",
    "evidence_truncated",
    "evidence_status",
    "evidence_error_stage",
    "evidence_error_type",
    "evidence_error_message",
    "source_size_before",
    "source_mtime_ns_before",
    "source_size_after",
    "source_mtime_ns_after",
    "source_changed_during_evidence",
    "evidence_revision",
)


def _string(name: str) -> pa.Field:
    return pa.field(name, pa.string(), nullable=True)


def _integer(name: str) -> pa.Field:
    return pa.field(name, pa.int64(), nullable=True)


def _boolean(name: str) -> pa.Field:
    return pa.field(name, pa.bool_(), nullable=True)


def calibration_sample_schema() -> pa.Schema:
    return pa.schema(
        [
            _string("phase2_run_id"),
            _string("calibration_sample_id"),
            _string("calibration_item_id"),
            _string("sample_role"),
            _string("pool_name"),
            _string("file_instance_id"),
            _string("sha256"),
            _string("source_root_id"),
            _string("relative_path"),
            _string("parent_group"),
            _string("file_name"),
            _integer("size_bytes"),
            _integer("mtime_ns"),
            _string("inventory_status"),
            _string("pdf_open_status"),
            _string("pdf_status"),
            _integer("page_count"),
            _string("text_layer_status"),
            _string("filename_parse_status"),
            _string("exact_duplicate_group_id"),
            _boolean("exact_duplicate_representative"),
            _integer("group_population"),
            _integer("group_quota"),
            _integer("selection_rank_or_index"),
            _string("sampling_method"),
            _string("full_inventory_run_id"),
            _string("inventory_schema_version"),
        ]
    )


def _atomic_write_text(text: str, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            descriptor = -1
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output)
    finally:
        if descriptor != -1:
            os.close(descriptor)
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    lines = [
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")


def write_jsonl_atomic(rows: Iterable[dict[str, Any]], path: str | Path) -> None:
    _atomic_write_text(jsonl_bytes(rows).decode("utf-8"), path)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL line at {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL line {line_number} is not an object")
            rows.append(value)
    return rows


def write_manifest_with_checksums(run_directory: str | Path, manifest: dict[str, Any]) -> None:
    """Write a Phase 2 manifest using the established normalized self-hash convention."""

    run_directory = Path(run_directory)
    descriptors_by_name = {
        name: artifact_descriptor(run_directory / name)
        for name in PHASE2_ARTIFACT_NAMES
        if name != "manifest.json"
    }
    checksum_basis = "manifest.json with its own sha256 normalized to 64 zeroes"
    self_descriptor: dict[str, Any] = {
        "path": "manifest.json",
        "size_bytes": 0,
        "sha256": "0" * 64,
        "checksum_basis": checksum_basis,
    }
    manifest["output_artifacts"] = [
        self_descriptor if name == "manifest.json" else descriptors_by_name[name]
        for name in PHASE2_ARTIFACT_NAMES
    ]

    size_guess = 0
    for _ in range(10):
        self_descriptor["size_bytes"] = size_guess
        size_value = len(json_bytes(manifest))
        if size_value == size_guess:
            break
        size_guess = size_value
    else:  # pragma: no cover - JSON size converges immediately
        raise ValueError("could not stabilize Phase 2 manifest checksum size")

    self_descriptor["size_bytes"] = size_guess
    self_descriptor["sha256"] = hashlib.sha256(json_bytes(manifest)).hexdigest()
    final_bytes = json_bytes(manifest)
    if len(final_bytes) != size_guess:  # pragma: no cover - digest length is fixed
        raise ValueError("Phase 2 manifest checksum size changed unexpectedly")
    write_json_atomic(manifest, run_directory / "manifest.json")


def write_phase2_artifacts(
    run_directory: str | Path,
    sample_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    statistics: dict[str, Any],
) -> None:
    """Write only the four Gate 2B canonical artifacts."""

    run_directory = Path(run_directory)
    write_parquet_atomic(
        sample_rows,
        run_directory / "calibration_sample.parquet",
        calibration_sample_schema(),
    )
    write_jsonl_atomic(evidence_rows, run_directory / "calibration_evidence.jsonl")
    write_json_atomic(statistics, run_directory / "statistics.json")
    write_manifest_with_checksums(run_directory, manifest)


def _normalized_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    normalized = dict(manifest)
    descriptors = normalized.get("output_artifacts")
    if not isinstance(descriptors, list):
        raise ValueError("manifest output_artifacts must be a list")
    normalized["output_artifacts"] = [
        {
            **item,
            "sha256": "0" * 64,
        }
        if isinstance(item, dict) and item.get("path") == "manifest.json"
        else item
        for item in descriptors
    ]
    return json_bytes(normalized)


def validate_phase2_artifacts(
    run_directory: str | Path,
    *,
    expected_sample_count: int | None = None,
) -> dict[str, Any]:
    """Validate schemas, row/order accounting, and all four artifact checksums."""

    run_directory = Path(run_directory)
    missing = [
        name for name in PHASE2_ARTIFACT_NAMES if not (run_directory / name).is_file()
    ]
    if missing:
        raise ValueError("Phase 2 canonical artifacts are missing: " + ", ".join(missing))

    sample_table = pq.read_table(run_directory / "calibration_sample.parquet")
    if not sample_table.schema.equals(calibration_sample_schema()):
        raise ValueError("calibration_sample.parquet schema validation failed")
    sample_rows = sample_table.to_pylist()
    if expected_sample_count is not None and len(sample_rows) != expected_sample_count:
        raise ValueError(
            f"calibration_sample.parquet row count mismatch: {len(sample_rows)} != {expected_sample_count}"
        )

    evidence_rows = read_jsonl(run_directory / "calibration_evidence.jsonl")
    if len(evidence_rows) != len(sample_rows):
        raise ValueError("calibration evidence row count does not match sample row count")
    sample_ids = [row.get("calibration_item_id") for row in sample_rows]
    evidence_ids = [row.get("calibration_item_id") for row in evidence_rows]
    if sample_ids != evidence_ids:
        raise ValueError("calibration evidence order does not match sample order")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("calibration sample contains duplicate calibration_item_id")
    if any(
        field not in row for row in evidence_rows for field in EVIDENCE_JSONL_FIELDS
    ):
        raise ValueError("calibration evidence row is missing a required field")

    with (run_directory / "manifest.json").open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    with (run_directory / "statistics.json").open("r", encoding="utf-8") as handle:
        statistics = json.load(handle)
    if not isinstance(manifest, dict) or not isinstance(statistics, dict):
        raise ValueError("manifest and statistics must be JSON objects")
    descriptors = manifest.get("output_artifacts")
    if not isinstance(descriptors, list):
        raise ValueError("manifest output_artifacts must be a list")
    descriptor_by_name = {
        item.get("path"): item for item in descriptors if isinstance(item, dict)
    }
    if set(descriptor_by_name) != set(PHASE2_ARTIFACT_NAMES):
        raise ValueError("Phase 2 manifest artifact path set validation failed")
    for name in PHASE2_ARTIFACT_NAMES:
        path = run_directory / name
        descriptor = descriptor_by_name[name]
        if descriptor.get("size_bytes") != path.stat().st_size:
            raise ValueError(f"Phase 2 artifact size validation failed: {name}")
        if name != "manifest.json" and descriptor.get("sha256") != sha256_path(path):
            raise ValueError(f"Phase 2 artifact SHA-256 validation failed: {name}")
    manifest_descriptor = descriptor_by_name["manifest.json"]
    if manifest_descriptor.get("sha256") != hashlib.sha256(
        _normalized_manifest_bytes(manifest)
    ).hexdigest():
        raise ValueError("Phase 2 normalized manifest SHA-256 validation failed")

    return {
        "status": "passed",
        "canonical_artifact_count": len(PHASE2_ARTIFACT_NAMES),
        "sample_rows": len(sample_rows),
        "evidence_rows": len(evidence_rows),
        "schema_validation": "passed",
        "row_accounting": "passed",
        "checksum_validation": "passed",
    }
