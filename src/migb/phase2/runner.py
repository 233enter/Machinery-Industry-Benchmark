"""Gate 2B orchestration: canonical-input validation, sampling, and Evidence."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import socket
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import pyarrow.parquet as pq

from migb.inventory.artifacts import (
    ARTIFACT_NAMES as INVENTORY_ARTIFACT_NAMES,
    json_bytes,
    sha256_path,
)
from migb.inventory.safety import assert_output_path_safe
from migb.inventory.schema import (
    FULL_INVENTORY_SCHEMA_VERSION,
    duplicate_groups_schema,
    errors_schema,
    files_schema,
)

from .artifacts import (
    PHASE2_ARTIFACT_NAMES,
    PHASE2_SCHEMA_VERSION,
    validate_phase2_artifacts,
    write_phase2_artifacts,
)
from .config import Phase2Config
from .evidence import EVIDENCE_REVISION, extract_evidence
from .sampling import (
    CalibrationSelection,
    build_calibration_selection,
    canonical_selection_bytes,
    sample_rows,
)


class Phase2Error(RuntimeError):
    """Raised when a Phase 2 run cannot safely start or complete."""


SAMPLING_CONTRACT_REVISION = "phase2-sampling-v0.1"
EXPECTED_FULL_FILE_COUNT = 60454
EXPECTED_FULL_RUN_STATUS = "completed"
EXPECTED_FULL_VERDICT = "PASS"


@dataclass(frozen=True)
class Phase2RunResult:
    run_id: str
    run_directory: Path
    manifest: dict[str, Any]
    statistics: dict[str, Any]
    artifact_validation: dict[str, Any]
    gate2b_verdict: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json_mapping(path: Path, description: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise Phase2Error(f"cannot read {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Phase2Error(f"{description} {path} must contain a JSON object")
    return value


def _git_provenance(repo_root: Path) -> tuple[str, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return commit, dirty
    except (OSError, subprocess.SubprocessError):
        return "unknown", True


def _tool_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for distribution in ("PyMuPDF", "pyarrow", "PyYAML"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = "not_installed"
    return versions


def _validate_simple_run_id(run_id: str) -> None:
    if (
        not isinstance(run_id, str)
        or not run_id
        or Path(run_id).name != run_id
        or not run_id.startswith("p2b-")
    ):
        raise Phase2Error("Phase 2 run ID must be a simple p2b- run ID")


def _verify_manifest_artifacts(
    root: Path,
    manifest: dict[str, Any],
    artifact_names: Iterable[str],
) -> dict[str, dict[str, Any]]:
    descriptors = manifest.get("output_artifacts")
    if not isinstance(descriptors, list):
        raise Phase2Error("Full Inventory manifest output_artifacts must be a list")
    descriptor_by_name = {
        item.get("path"): item for item in descriptors if isinstance(item, dict)
    }
    expected_names = set(artifact_names)
    if set(descriptor_by_name) != expected_names:
        raise Phase2Error("Full Inventory manifest artifact path set validation failed")

    for name in artifact_names:
        path = root / name
        descriptor = descriptor_by_name[name]
        if not path.is_file():
            raise Phase2Error(f"Full Inventory artifact is missing: {path}")
        if descriptor.get("size_bytes") != path.stat().st_size:
            raise Phase2Error(f"Full Inventory artifact size validation failed: {name}")
        if name != "manifest.json" and descriptor.get("sha256") != sha256_path(path):
            raise Phase2Error(f"Full Inventory artifact SHA-256 validation failed: {name}")

    manifest_descriptor = descriptor_by_name["manifest.json"]
    normalized = dict(manifest)
    normalized["output_artifacts"] = [
        {
            **item,
            "sha256": "0" * 64,
        }
        if isinstance(item, dict) and item.get("path") == "manifest.json"
        else item
        for item in descriptors
    ]
    if manifest_descriptor.get("sha256") != _sha256_bytes(json_bytes(normalized)):
        raise Phase2Error("Full Inventory normalized manifest SHA-256 validation failed")
    return descriptor_by_name


def validate_full_inventory(config: Phase2Config) -> dict[str, Any]:
    """Validate the immutable Full Inventory before reading selection records."""

    root = config.input.inventory_root
    if root.name != config.input.inventory_run_id:
        raise Phase2Error("inventory_root basename must equal input.inventory_run_id")
    if not root.is_dir():
        raise Phase2Error(f"Full Inventory root is not an accessible directory: {root}")

    manifest = _read_json_mapping(root / "manifest.json", "Full Inventory manifest")
    if manifest.get("inventory_run_id") != config.input.inventory_run_id:
        raise Phase2Error("Full Inventory Run ID does not match Phase 2 config")
    if manifest.get("inventory_schema_version") != FULL_INVENTORY_SCHEMA_VERSION:
        raise Phase2Error("Full Inventory schema is not inventory-v0.2")
    if manifest.get("run_status") != EXPECTED_FULL_RUN_STATUS:
        raise Phase2Error("Full Inventory run_status is not completed")
    if manifest.get("full_inventory_verdict") != EXPECTED_FULL_VERDICT:
        raise Phase2Error("Full Inventory verdict is not PASS")
    if manifest.get("dirty") is not False:
        raise Phase2Error("Full Inventory Git dirty state is not false")
    if manifest.get("migb_data_root") != str(config.input.migb_data_root):
        raise Phase2Error("Full Inventory MIGB_DATA_ROOT does not match Phase 2 config")

    source_roots = manifest.get("source_roots")
    if not isinstance(source_roots, list) or len(source_roots) != 1:
        raise Phase2Error("Full Inventory must contain exactly one configured source root")
    if source_roots[0].get("path") != str(config.input.source_root):
        raise Phase2Error("Full Inventory source root does not match Phase 2 config")

    descriptors = _verify_manifest_artifacts(root, manifest, INVENTORY_ARTIFACT_NAMES)
    artifact_validation = manifest.get("artifact_validation")
    if not isinstance(artifact_validation, dict) or any(
        artifact_validation.get(key) != "passed"
        for key in ("checksum_validation", "row_accounting", "schema_validation", "status")
    ):
        raise Phase2Error("Full Inventory manifest does not report passed Artifact validation")

    try:
        files_table = pq.read_table(root / "files.parquet")
        duplicate_table = pq.read_table(root / "duplicate_groups.parquet")
        errors_table = pq.read_table(root / "errors.parquet")
    except Exception as exc:  # pyarrow can raise several file/schema exceptions.
        raise Phase2Error(f"cannot read Full Inventory Parquet artifacts: {exc}") from exc
    if not files_table.schema.equals(files_schema()):
        raise Phase2Error("Full Inventory files.parquet schema validation failed")
    if not duplicate_table.schema.equals(duplicate_groups_schema()):
        raise Phase2Error("Full Inventory duplicate_groups.parquet schema validation failed")
    if not errors_table.schema.equals(errors_schema()):
        raise Phase2Error("Full Inventory errors.parquet schema validation failed")
    if files_table.num_rows != EXPECTED_FULL_FILE_COUNT:
        raise Phase2Error(
            f"Full Inventory files.parquet rows {files_table.num_rows} != {EXPECTED_FULL_FILE_COUNT}"
        )

    statistics = _read_json_mapping(root / "statistics.json", "Full Inventory statistics")
    if statistics.get("processed_files") != EXPECTED_FULL_FILE_COUNT:
        raise Phase2Error("Full Inventory processed_files is not 60454")
    if statistics.get("full_inventory_verdict") != EXPECTED_FULL_VERDICT:
        raise Phase2Error("Full Inventory statistics verdict is not PASS")

    return {
        "run_id": config.input.inventory_run_id,
        "root": root,
        "manifest": manifest,
        "statistics": statistics,
        "records": files_table.to_pylist(),
        "duplicate_rows": duplicate_table.to_pylist(),
        "errors": errors_table.to_pylist(),
        "artifact_descriptors": descriptors,
        "artifact_validation": {
            "status": "passed",
            "checksum_validation": "passed",
            "row_accounting": "passed",
            "schema_validation": "passed",
        },
    }


def _calibration_sample_id(config: Phase2Config) -> str:
    import uuid

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            "migb://phase2/calibration-sample/"
            f"{config.input.inventory_run_id}/{config.fingerprint()}/{SAMPLING_CONTRACT_REVISION}",
        )
    )


def _safe_source_path(source_root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise Phase2Error("selected Source record has an empty relative_path")
    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or any(part in {"", ".."} for part in relative.parts):
        raise Phase2Error(f"unsafe selected relative_path: {relative_path!r}")
    candidate = source_root.joinpath(*relative.parts)
    if candidate.is_symlink():
        raise Phase2Error(f"selected Source path is a symlink: {candidate}")
    source_resolved = source_root.resolve(strict=False)
    candidate_resolved = candidate.resolve(strict=False)
    try:
        candidate_resolved.relative_to(source_resolved)
    except ValueError as exc:
        raise Phase2Error(f"selected Source path escapes source root: {relative_path!r}") from exc
    if not candidate.is_file():
        raise Phase2Error(f"selected Source path is not a regular file: {candidate}")
    return candidate


def _prepare_evidence_tasks(
    sample_rows_value: list[dict[str, Any]],
    config: Phase2Config,
) -> tuple[list[dict[str, Any]], int]:
    tasks: list[dict[str, Any]] = []
    mismatch_count = 0
    for row in sample_rows_value:
        path = _safe_source_path(config.input.source_root, str(row["relative_path"]))
        try:
            stat_result = path.stat()
        except OSError as exc:
            raise Phase2Error(f"cannot stat selected Source path {path}: {exc}") from exc
        expected_size = row.get("size_bytes")
        expected_mtime = row.get("mtime_ns")
        if (
            expected_size is None
            or expected_mtime is None
            or stat_result.st_size != expected_size
            or stat_result.st_mtime_ns != expected_mtime
        ):
            mismatch_count += 1
        tasks.append(
            {
                "source_path": str(path),
                "phase2_run_id": row["phase2_run_id"],
                "calibration_sample_id": row["calibration_sample_id"],
                "calibration_item_id": row["calibration_item_id"],
                "file_instance_id": row["file_instance_id"],
                "pool_name": row["pool_name"],
                "relative_path": row["relative_path"],
                "parent_group": row["parent_group"],
                "sha256": row.get("sha256"),
                "page_count": row.get("page_count"),
                "text_layer_status": row.get("text_layer_status"),
                "filename_title": None,
                "metadata_title": None,
                "expected_size_bytes": expected_size,
                "expected_mtime_ns": expected_mtime,
                "page_indices": list(config.evidence.page_indices),
                "max_extracted_chars": config.evidence.max_extracted_chars,
                "evidence_revision": EVIDENCE_REVISION,
                "not_applicable": row["pool_name"] == "source_quality_exception",
            }
        )
    if mismatch_count:
        raise Phase2Error(
            f"pre-extraction Source mismatch count is {mismatch_count}; stopping Gate 2B"
        )
    return tasks, mismatch_count


def _quota_dict(quota: Any) -> dict[str, Any]:
    return {
        "parent_group": quota.parent_group,
        "population": quota.population,
        "base_quota": quota.base_quota,
        "proportional_quota": quota.proportional_quota,
        "remainder": float(quota.remainder),
        "largest_remainder_award": quota.largest_remainder_award,
        "final_quota": quota.final_quota,
        "actual_selected_count": quota.actual_selected_count,
    }


def _char_distribution(values: list[int]) -> dict[str, int | None]:
    if not values:
        return {key: None for key in ("min", "p10", "median", "p90", "max")}
    ordered = sorted(values)

    def percentile(index_fraction: float) -> int:
        index = int(round((len(ordered) - 1) * index_fraction))
        return ordered[index]

    return {
        "min": ordered[0],
        "p10": percentile(0.10),
        "median": percentile(0.50),
        "p90": percentile(0.90),
        "max": ordered[-1],
    }


def _evidence_scope_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(row.get("evidence_status") for row in rows)
    char_values = [int(row.get("evidence_char_count") or 0) for row in rows]
    non_exception = [
        row
        for row in rows
        if row.get("evidence_status") in {"success", "partial"}
    ]
    metadata_count = sum(bool(str(row.get("metadata_title") or "").strip()) for row in rows)
    filename_count = sum(bool(str(row.get("filename_title") or "").strip()) for row in rows)
    return {
        "count": len(rows),
        "evidence_success_count": status_counts.get("success", 0),
        "evidence_partial_count": status_counts.get("partial", 0),
        "evidence_failed_count": status_counts.get("failed", 0),
        "evidence_not_applicable_count": status_counts.get("not_applicable", 0),
        "evidence_char_count": _char_distribution(char_values),
        "evidence_truncated_count": sum(bool(row.get("evidence_truncated")) for row in rows),
        "zero_text_evidence_count": sum(
            int(row.get("raw_text_char_count") or 0) == 0 for row in non_exception
        ),
        "metadata_title_present_count": metadata_count,
        "metadata_title_present_rate": metadata_count / len(rows) if rows else 0.0,
        "filename_title_present_count": filename_count,
        "filename_title_present_rate": filename_count / len(rows) if rows else 0.0,
        "source_changed_during_evidence_count": sum(
            bool(row.get("source_changed_during_evidence")) for row in rows
        ),
    }


def _gate2b_verdict(
    *,
    selection: CalibrationSelection,
    sample_rows_value: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    recomputation_passed: bool,
    pre_extraction_source_mismatch_count: int,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    main_pool = next(pool for pool in selection.pools if pool.pool_name == "main")
    if main_pool.actual_count != main_pool.target:
        reasons.append("Main Sample actual count does not reach target")
    if len(sample_rows_value) != len(evidence_rows):
        reasons.append("sample/evidence row accounting mismatch")
    if selection.main_audit_overlap_count or selection.cross_pool_overlap_count:
        reasons.append("Main/Audit or Audit/Audit overlap is non-zero")
    if not recomputation_passed:
        reasons.append("deterministic recomputation failed")
    if pre_extraction_source_mismatch_count:
        reasons.append("pre-extraction Source mismatch was detected")
    if any(row.get("source_changed_during_evidence") for row in evidence_rows):
        reasons.append("Source changed during Evidence extraction")
    if any(row.get("evidence_status") == "failed" for row in evidence_rows):
        reasons.append("unexplained Evidence extraction failure")
    if len({row.get("calibration_item_id") for row in sample_rows_value}) != len(sample_rows_value):
        reasons.append("duplicate calibration_item_id")
    return ("PASS" if not reasons else "FAIL"), reasons


def _statistics(
    selection: CalibrationSelection,
    sample_rows_value: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    *,
    recomputation_passed: bool,
    calibration_sample_hash: str,
    pre_extraction_source_mismatch_count: int,
    gate2b_verdict: str,
    gate2b_verdict_reasons: list[str],
    full_inventory_validation: dict[str, Any],
) -> dict[str, Any]:
    pool_stats = {}
    for pool in selection.pools:
        pool_stats[pool.pool_name] = {
            "target": pool.target,
            "actual": pool.actual_count,
            "candidate_count": pool.candidate_count,
            "per_parent_group": [_quota_dict(quota) for quota in pool.group_quotas],
        }
    evidence_by_pool = {
        pool_name: _evidence_scope_metrics(
            [row for row in evidence_rows if row.get("pool_name") == pool_name]
        )
        for pool_name in ("main", "source_quality_exception", "text_absent", "mixed_text", "filename_unmatched")
    }
    evidence_by_parent_group = {
        group: _evidence_scope_metrics(
            [row for row in evidence_rows if row.get("parent_group") == group]
        )
        for group in sorted({str(row.get("parent_group")) for row in evidence_rows})
    }
    overall_evidence = _evidence_scope_metrics(evidence_rows)
    main_pool = pool_stats["main"]
    audit_targets = {
        name: pool_stats[name]["target"]
        for name in pool_stats
        if name != "main"
    }
    audit_actuals = {
        name: pool_stats[name]["actual"]
        for name in pool_stats
        if name != "main"
    }
    return {
        "run_status": "completed",
        "stage": "gate2b",
        "gate2b_verdict": gate2b_verdict,
        "gate2b_verdict_reasons": gate2b_verdict_reasons,
        "main_target": main_pool["target"],
        "main_actual": main_pool["actual"],
        "main_per_parent_group": main_pool["per_parent_group"],
        "source_quality_exception_target": audit_targets["source_quality_exception"],
        "source_quality_exception_actual": audit_actuals["source_quality_exception"],
        "text_absent_target": audit_targets["text_absent"],
        "text_absent_actual": audit_actuals["text_absent"],
        "text_absent_per_parent_group": pool_stats["text_absent"]["per_parent_group"],
        "mixed_text_target": audit_targets["mixed_text"],
        "mixed_text_actual": audit_actuals["mixed_text"],
        "mixed_text_per_parent_group": pool_stats["mixed_text"]["per_parent_group"],
        "filename_unmatched_target": audit_targets["filename_unmatched"],
        "filename_unmatched_actual": audit_actuals["filename_unmatched"],
        "filename_unmatched_per_parent_group": pool_stats["filename_unmatched"]["per_parent_group"],
        "audit_targets": audit_targets,
        "audit_actuals": audit_actuals,
        "total_unique_selected": len(selection.items),
        "main_audit_overlap_count": selection.main_audit_overlap_count,
        "cross_pool_overlap_count": selection.cross_pool_overlap_count,
        "physical_eligible_count": selection.main_physical_eligible_count,
        "physical_eligible_population": selection.main_physical_eligible_count,
        "duplicate_collapsed_eligible_count": selection.main_duplicate_collapsed_eligible_count,
        "duplicate_collapsed_eligible_population": selection.main_duplicate_collapsed_eligible_count,
        "exact_duplicates_excluded_from_sampling": selection.exact_duplicates_excluded_from_sampling,
        "calibration_sample_id": sample_rows_value[0]["calibration_sample_id"] if sample_rows_value else None,
        "calibration_sample_hash": calibration_sample_hash,
        "deterministic_recomputation_passed": recomputation_passed,
        "pre_extraction_source_mismatch_count": pre_extraction_source_mismatch_count,
        "post_extraction_source_changed_count": overall_evidence["source_changed_during_evidence_count"],
        "evidence_success_count": overall_evidence["evidence_success_count"],
        "evidence_partial_count": overall_evidence["evidence_partial_count"],
        "evidence_failed_count": overall_evidence["evidence_failed_count"],
        "evidence_not_applicable_count": overall_evidence["evidence_not_applicable_count"],
        "zero_text_evidence_count": overall_evidence["zero_text_evidence_count"],
        "evidence_truncated_count": overall_evidence["evidence_truncated_count"],
        "evidence_char_count": overall_evidence["evidence_char_count"],
        "metadata_title_present_count": overall_evidence["metadata_title_present_count"],
        "metadata_title_present_rate": overall_evidence["metadata_title_present_rate"],
        "filename_title_present_count": overall_evidence["filename_title_present_count"],
        "filename_title_present_rate": overall_evidence["filename_title_present_rate"],
        "evidence_by_pool": evidence_by_pool,
        "evidence_by_parent_group": evidence_by_parent_group,
        "full_inventory_artifact_integrity": full_inventory_validation["artifact_validation"],
        "sample_row_count": len(sample_rows_value),
        "evidence_row_count": len(evidence_rows),
    }


def _evidence_tasks_with_titles(
    tasks: list[dict[str, Any]],
    sample_rows_value: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {row["calibration_item_id"]: row for row in sample_rows_value}
    for task in tasks:
        row = by_id[task["calibration_item_id"]]
        task["filename_title"] = row.get("filename_title")
        task["metadata_title"] = row.get("metadata_title")
    return tasks


def run_phase2(
    config: Phase2Config,
    *,
    repo_root: str | Path = ".",
    run_id: str | None = None,
) -> Phase2RunResult:
    """Run Gate 2B and stop after writing/validating its four artifacts."""

    full_inventory = validate_full_inventory(config)
    assert_output_path_safe(
        [config.input.source_root],
        config.input.migb_data_root,
    )
    if not config.input.source_root.is_dir():
        raise Phase2Error(f"Source root is not an accessible directory: {config.input.source_root}")

    repo_root = Path(repo_root).resolve()
    git_commit, dirty = _git_provenance(repo_root)
    if run_id is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        git_suffix = git_commit[:7] if git_commit != "unknown" else "unknown"
        run_id = f"p2b-{timestamp}-{git_suffix}"
    _validate_simple_run_id(run_id)

    calibration_sample_id = _calibration_sample_id(config)
    selection_first = build_calibration_selection(
        full_inventory["records"],
        full_inventory["duplicate_rows"],
        main_target=config.sampling.main_target,
        base_quota_per_parent_group=config.sampling.base_quota_per_parent_group,
        audit_targets={
            "source_quality_exception": config.sampling.audit.source_quality_exception,
            "text_absent": config.sampling.audit.text_absent_target,
            "mixed_text": config.sampling.audit.mixed_text_target,
            "filename_unmatched": config.sampling.audit.filename_unmatched_target,
        },
        calibration_sample_id=calibration_sample_id,
    )
    selection_second = build_calibration_selection(
        full_inventory["records"],
        full_inventory["duplicate_rows"],
        main_target=config.sampling.main_target,
        base_quota_per_parent_group=config.sampling.base_quota_per_parent_group,
        audit_targets={
            "source_quality_exception": config.sampling.audit.source_quality_exception,
            "text_absent": config.sampling.audit.text_absent_target,
            "mixed_text": config.sampling.audit.mixed_text_target,
            "filename_unmatched": config.sampling.audit.filename_unmatched_target,
        },
        calibration_sample_id=calibration_sample_id,
    )
    recomputation_passed = (
        canonical_selection_bytes(selection_first) == canonical_selection_bytes(selection_second)
        and selection_first == selection_second
    )
    if not recomputation_passed:
        raise Phase2Error("deterministic sampling recomputation failed")
    selection = selection_first
    calibration_sample_hash = _sha256_bytes(canonical_selection_bytes(selection))
    sample_rows_value = sample_rows(
        selection,
        phase2_run_id=run_id,
        calibration_sample_id=calibration_sample_id,
        full_inventory_run_id=config.input.inventory_run_id,
        inventory_schema_version=FULL_INVENTORY_SCHEMA_VERSION,
    )

    evidence_tasks, pre_extraction_source_mismatch_count = _prepare_evidence_tasks(
        sample_rows_value,
        config,
    )
    evidence_tasks = _evidence_tasks_with_titles(evidence_tasks, sample_rows_value)

    output_root = config.input.migb_data_root.resolve(strict=False)
    run_directory = output_root / "phase2" / "runs" / run_id
    if run_directory.exists():
        raise Phase2Error(f"Phase 2 run ID already exists and is immutable: {run_directory}")
    run_directory.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_directory.mkdir()
    except FileExistsError as exc:
        raise Phase2Error(f"Phase 2 run ID already exists and is immutable: {run_directory}") from exc

    started_at = _utc_now()
    evidence_rows = extract_evidence(evidence_tasks, worker_count=config.evidence.worker_count)
    gate2b_verdict, gate2b_verdict_reasons = _gate2b_verdict(
        selection=selection,
        sample_rows_value=sample_rows_value,
        evidence_rows=evidence_rows,
        recomputation_passed=recomputation_passed,
        pre_extraction_source_mismatch_count=pre_extraction_source_mismatch_count,
    )
    completed_at = _utc_now()
    statistics = _statistics(
        selection,
        sample_rows_value,
        evidence_rows,
        recomputation_passed=recomputation_passed,
        calibration_sample_hash=calibration_sample_hash,
        pre_extraction_source_mismatch_count=pre_extraction_source_mismatch_count,
        gate2b_verdict=gate2b_verdict,
        gate2b_verdict_reasons=gate2b_verdict_reasons,
        full_inventory_validation=full_inventory,
    )
    manifest: dict[str, Any] = {
        "phase2_run_id": run_id,
        "stage": "gate2b",
        "schema_version": PHASE2_SCHEMA_VERSION,
        "run_status": "completed",
        "hostname": socket.gethostname(),
        "git_commit": git_commit,
        "dirty": dirty,
        "python_version": platform.python_version(),
        "tool_versions": _tool_versions(),
        "full_inventory_run_id": config.input.inventory_run_id,
        "full_inventory_artifact_checksums": full_inventory["artifact_descriptors"],
        "full_inventory_artifact_integrity": full_inventory["artifact_validation"],
        "config_snapshot": config.snapshot(),
        "config_fingerprint": config.fingerprint(),
        "sampling_contract_revision": SAMPLING_CONTRACT_REVISION,
        "evidence_revision": EVIDENCE_REVISION,
        "main_target": statistics["main_target"],
        "main_actual": statistics["main_actual"],
        "audit_targets": statistics["audit_targets"],
        "audit_actuals": statistics["audit_actuals"],
        "total_unique_selected": statistics["total_unique_selected"],
        "physical_eligible_count": statistics["physical_eligible_count"],
        "duplicate_collapsed_eligible_count": statistics["duplicate_collapsed_eligible_count"],
        "exact_duplicates_excluded_from_sampling": statistics[
            "exact_duplicates_excluded_from_sampling"
        ],
        "calibration_sample_id": calibration_sample_id,
        "calibration_sample_hash": calibration_sample_hash,
        "deterministic_recomputation_passed": recomputation_passed,
        "pre_extraction_source_mismatch_count": pre_extraction_source_mismatch_count,
        "post_extraction_source_changed_count": statistics[
            "post_extraction_source_changed_count"
        ],
        "worker_count": config.evidence.worker_count,
        "started_at": started_at,
        "completed_at": completed_at,
        "gate2b_verdict": gate2b_verdict,
        "gate2b_verdict_reasons": gate2b_verdict_reasons,
        "output_artifacts": [],
    }
    write_phase2_artifacts(
        run_directory,
        sample_rows_value,
        evidence_rows,
        manifest,
        statistics,
    )
    try:
        artifact_validation = validate_phase2_artifacts(
            run_directory,
            expected_sample_count=len(sample_rows_value),
        )
    except (OSError, ValueError) as exc:
        raise Phase2Error(f"Gate 2B artifact validation failed: {exc}") from exc
    return Phase2RunResult(
        run_id=run_id,
        run_directory=run_directory,
        manifest=manifest,
        statistics=statistics,
        artifact_validation=artifact_validation,
        gate2b_verdict=gate2b_verdict,
    )
