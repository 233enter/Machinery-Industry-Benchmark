"""D1 runner with process-isolated PyMuPDF work."""

from __future__ import annotations

import importlib.metadata
import hashlib
import json
import math
import os
import platform
import shutil
import socket
import subprocess
import time
from collections import Counter
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .artifacts import (
    ARTIFACT_NAMES,
    artifact_descriptor,
    create_run_directory,
    group_exact_duplicates,
    json_bytes,
    sha256_path,
    write_d1_artifacts,
    write_json_atomic,
    write_parquet,
    write_parquet_atomic,
)
from .config import EnvironmentConfig
from .discovery import (
    DiscoveredFile,
    DiscoveryError,
    SourceSnapshot,
    capture_source_snapshot,
    compare_source_snapshots,
    discover_pdfs,
)
from .filename_parser import parse_filename
from .hashing import sha256_file
from .identity import file_instance_id
from .pdf_inspector import inspect_pdf
from .safety import SafetyError, assert_output_path_safe
from .sampling import (
    D1Sample,
    D2Sample,
    D3Sample,
    D3_TARGET_SAMPLE_COUNT,
    select_d1,
    select_d2,
    select_d3,
)
from .schema import (
    FULL_INVENTORY_SCHEMA_VERSION,
    INVENTORY_SCHEMA_VERSION,
    duplicate_groups_schema,
    errors_schema,
    files_schema,
)


class PipelineError(RuntimeError):
    """Raised when a D1 run cannot be started or completed safely."""


D3_CHECKPOINT_BATCH_SIZE = 100
D3_DEFAULT_CHECKPOINT_BATCH_SIZE = D3_CHECKPOINT_BATCH_SIZE
FULL_CHECKPOINT_BATCH_SIZE = 500
D3_MAX_RETRIES = 2
D3_MAX_RETRIES_TOTAL_ATTEMPTS = D3_MAX_RETRIES + 1
D3_RETRY_BACKOFF_SECONDS = (0.5, 2.0)
D3_RUN_STATES = frozenset({"running", "interrupted", "completed", "failed"})
FULL_RUN_STATES = D3_RUN_STATES
FULL_SELECTION_METHOD = "all_eligible_pdf_in_configured_source_root"
FULL_EXPECTED_PDF_COUNT = 60454
FULL_EXPECTED_TOP_LEVEL_GROUP_COUNT = 20
FULL_MAX_UNMATCHED_FILENAME_EXAMPLES = 20


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _error_row(task: dict[str, Any], run_id: str, error: dict[str, str]) -> dict[str, str]:
    return {
        "inventory_run_id": run_id,
        "file_instance_id": task["file_instance_id"],
        "source_root_id": task["source_root_id"],
        "relative_path": task["relative_path"],
        "stage": error["stage"],
        "error_category": error["error_category"],
        "error_message": error["error_message"],
        "timestamp": error.get("timestamp", _utc_now()),
    }


def _task_for(
    item: DiscoveredFile,
    threshold: int,
    run_id: str,
    *,
    inventory_schema_version: str = INVENTORY_SCHEMA_VERSION,
    classify_zero_page_as_invalid: bool = False,
) -> dict[str, Any]:
    return {
        "path": str(item.path),
        "source_root_id": item.source_root_id,
        "relative_path": item.relative_path,
        "file_name": item.file_name,
        "parent_group": item.parent_group,
        "extension": item.extension,
        "file_instance_id": file_instance_id(item.source_root_id, item.relative_path),
        "text_page_char_threshold": threshold,
        "inventory_schema_version": inventory_schema_version,
        "classify_zero_page_as_invalid": classify_zero_page_as_invalid,
        "inventory_run_id": run_id,
        "collected_at": _utc_now(),
    }


def _base_record(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "inventory_schema_version": task.get(
            "inventory_schema_version", INVENTORY_SCHEMA_VERSION
        ),
        "file_instance_id": task["file_instance_id"],
        "source_root_id": task["source_root_id"],
        "relative_path": task["relative_path"],
        "file_name": task["file_name"],
        "parent_group": task["parent_group"],
        "extension": task["extension"],
        "size_bytes": None,
        "mtime_ns": None,
        "source_changed_during_run": False,
        "sha256": None,
        "hash_status": "not_attempted",
        "pdf_open_status": "not_attempted",
        "pdf_error_category": None,
        "pdf_status": "unknown",
        "is_encrypted": None,
        "pdf_version": None,
        "page_count": None,
        "metadata_title": None,
        "metadata_author": None,
        "metadata_subject": None,
        "metadata_keywords": None,
        "metadata_creator": None,
        "metadata_producer": None,
        "metadata_creation_date": None,
        "metadata_modification_date": None,
        "sampled_page_count": 0,
        "sampled_text_char_count": 0,
        "text_layer_status": "check_failed",
        "filename_year": None,
        "filename_issue": None,
        "filename_title": None,
        "filename_parse_status": "error",
        "inventory_status": "failed",
        "collected_at": task["collected_at"],
        "inventory_run_id": task["inventory_run_id"],
    }


def _task_error(stage: str, category: str, exc: BaseException) -> dict[str, str]:
    return {
        "stage": stage,
        "error_category": category,
        "error_message": f"{type(exc).__name__}: {exc}",
        "timestamp": _utc_now(),
    }


def process_file_task(task: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Process one file in one process; no PyMuPDF Document crosses the boundary."""

    record = _base_record(task)
    errors: list[dict[str, str]] = []
    path = Path(task["path"])
    stat_before = None

    try:
        stat_before = path.stat()
        record["size_bytes"] = stat_before.st_size
        record["mtime_ns"] = stat_before.st_mtime_ns
    except OSError as exc:
        errors.append(_task_error("stat_before", type(exc).__name__, exc))

    if stat_before is not None:
        try:
            record["sha256"] = sha256_file(path)
            record["hash_status"] = "success"
        except OSError as exc:
            record["hash_status"] = "failed"
            errors.append(_task_error("hash", type(exc).__name__, exc))

        inspection = inspect_pdf(
            path.as_posix(),
            task["text_page_char_threshold"],
            classify_zero_page_as_invalid=bool(
                task.get("classify_zero_page_as_invalid", False)
                or task.get("inventory_schema_version")
                == FULL_INVENTORY_SCHEMA_VERSION
            ),
        )
        for key, value in inspection.items():
            if key != "errors":
                record[key] = value
        errors.extend(inspection["errors"])

    else:
        pass

    try:
        filename_result = parse_filename(task["file_name"])
        record.update(
            {
                "filename_year": filename_result.filename_year,
                "filename_issue": filename_result.filename_issue,
                "filename_title": filename_result.filename_title,
                "filename_parse_status": filename_result.filename_parse_status,
            }
        )
    except Exception as exc:  # pragma: no cover - parser is intentionally defensive
        record["filename_parse_status"] = "error"
        errors.append(_task_error("filename_parse", type(exc).__name__, exc))

    if stat_before is not None:
        try:
            stat_after = path.stat()
            if (
                stat_before.st_size != stat_after.st_size
                or stat_before.st_mtime_ns != stat_after.st_mtime_ns
            ):
                record["source_changed_during_run"] = True
                errors.append(
                    _task_error(
                        "source_consistency",
                        "source_changed_during_run",
                        RuntimeError("size or mtime changed during file task"),
                    )
                )
        except OSError as exc:
            errors.append(_task_error("source_consistency", type(exc).__name__, exc))

    if errors:
        record["inventory_status"] = "partial" if stat_before is not None else "failed"
    else:
        record["inventory_status"] = "success"
    return record, errors


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


def _fallback_result(task: dict[str, Any], exc: BaseException) -> tuple[dict[str, Any], dict[str, str]]:
    record = _base_record(task)
    error = _task_error("worker", type(exc).__name__, exc)
    return record, error


@dataclass(frozen=True)
class D1RunResult:
    run_id: str
    run_directory: Path
    manifest: dict[str, Any]
    statistics: dict[str, Any]


def _active_roots_and_safe_output(config: EnvironmentConfig) -> tuple[list[Any], Path]:
    if config.inventory.worker_count != 4:
        raise PipelineError("D1/D2/D3/Full requires inventory.worker_count = 4")
    active_roots = [root for root in config.source_roots if root.enabled]
    if not active_roots:
        raise PipelineError("no enabled source roots")
    for source_root in active_roots:
        if not source_root.path.exists() or not source_root.path.is_dir():
            raise PipelineError(f"source root is not an accessible directory: {source_root.path}")

    # This must happen before create_run_directory or any output parent is created.
    output_root = assert_output_path_safe(
        [source_root.path for source_root in active_roots],
        config.migb_data_root,
    )
    return active_roots, output_root


def _discover_active_roots(active_roots: list[Any]) -> list[DiscoveredFile]:
    discovered: list[DiscoveredFile] = []
    for source_root in active_roots:
        try:
            discovered.extend(discover_pdfs(source_root.source_root_id, source_root.path))
        except DiscoveryError as exc:
            raise PipelineError(str(exc)) from exc
    return discovered


def _load_prior_sample_ids(config: EnvironmentConfig, prior_run_id: str) -> set[str]:
    """Load and validate the D1 sample identities used to isolate D2."""

    if not prior_run_id or Path(prior_run_id).name != prior_run_id or not prior_run_id.startswith("d1-"):
        raise PipelineError("prior_run_id must be a simple D1 run ID")

    manifest_path = (
        config.migb_data_root
        / "inventory"
        / "runs"
        / prior_run_id
        / "sample_manifest.json"
    )
    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"cannot read prior D1 sample manifest {manifest_path}: {exc}") from exc

    if not isinstance(manifest, dict) or manifest.get("inventory_run_id") != prior_run_id:
        raise PipelineError("prior sample manifest inventory_run_id does not match prior_run_id")
    items = manifest.get("items")
    if not isinstance(items, list):
        raise PipelineError("prior sample manifest items must be a list")

    excluded_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("file_instance_id"), str):
            raise PipelineError(f"prior sample manifest item {index} has no file_instance_id")
        excluded_ids.add(item["file_instance_id"])
    if not excluded_ids:
        raise PipelineError("prior D1 sample manifest contains no file_instance_id values")
    return excluded_ids


def _sample_manifest(
    stage: str,
    run_id: str,
    active_roots: list[Any],
    discovered: list[DiscoveredFile],
    sample: D1Sample | D2Sample,
    excluded_file_instance_ids: set[str],
    prior_run_id: str | None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "inventory_run_id": run_id,
        "source_root_id": active_roots[0].source_root_id if len(active_roots) == 1 else None,
        "sampling_method": sample.sampling_method,
        "sample_count": len(sample.items),
        "items": [
            {
                "source_root_id": item.source_root_id,
                "parent_group": item.parent_group,
                "file_instance_id": file_instance_id(item.source_root_id, item.relative_path),
                "relative_path": item.relative_path,
            }
            for item in sample.items
        ],
    }
    if stage != "d2":
        return manifest

    if not isinstance(sample, D2Sample):
        raise PipelineError("D2 sample must use D2Sample metadata")
    discovered_ids = {
        file_instance_id(item.source_root_id, item.relative_path) for item in discovered
    }
    manifest.update(
        {
            "sampling_stage": "d2",
            "sampling_method": sample.sampling_method,
            "excluded_prior_run_id": prior_run_id,
            "excluded_prior_sample_count": len(excluded_file_instance_ids),
            "excluded_prior_sample_found_count": len(
                excluded_file_instance_ids & discovered_ids
            ),
            "excluded_prior_sample_missing_count": len(
                excluded_file_instance_ids - discovered_ids
            ),
            "target_sample_count": sample.target_sample_count,
            "actual_sample_count": sample.actual_sample_count,
            "target_per_group_count": sample.target_per_group,
            "per_group_sample_count": [
                {
                    "source_root_id": source_root_id,
                    "parent_group": parent_group,
                    "target_count": sample.target_per_group,
                    "actual_count": actual_count,
                }
                for source_root_id, parent_group, actual_count in sample.per_group_sample_count
            ],
        }
    )
    for item in manifest["items"]:
        item["sampling_method"] = sample.sampling_method
    return manifest


def _run_stage(
    config: EnvironmentConfig,
    stage: str,
    repo_root: str | Path = ".",
    run_id: str | None = None,
    prior_run_id: str | None = None,
) -> D1RunResult:
    """Run one deterministic inventory dry-run stage and write all six Artifacts."""

    if stage not in {"d1", "d2"}:
        raise PipelineError(f"unsupported inventory stage: {stage}")
    active_roots, output_root = _active_roots_and_safe_output(config)
    excluded_file_instance_ids = (
        _load_prior_sample_ids(config, prior_run_id) if stage == "d2" and prior_run_id else set()
    )
    if stage == "d2" and not prior_run_id:
        raise PipelineError("D2 requires prior_run_id")

    started_at = _utc_now()
    started_clock = time.perf_counter()
    repo_root = Path(repo_root).resolve()
    git_commit, dirty = _git_provenance(repo_root)
    if run_id is None:
        git_suffix = git_commit[:7] if git_commit != "unknown" else "unknown"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{stage}-{timestamp}-{git_suffix}"

    run_directory = create_run_directory(output_root, run_id)

    discovered = _discover_active_roots(active_roots)
    if stage == "d1":
        sample: D1Sample | D2Sample = select_d1(discovered)
    else:
        sample = select_d2(discovered, excluded_file_instance_ids)
    tasks = [
        _task_for(item, config.inventory.text_page_char_threshold, run_id)
        for item in sample.items
    ]

    file_records: list[dict[str, Any]] = []
    error_rows: list[dict[str, str]] = []
    with ProcessPoolExecutor(max_workers=config.inventory.worker_count) as executor:
        future_to_task = {executor.submit(process_file_task, task): task for task in tasks}
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                record, task_errors = future.result()
            except Exception as exc:  # keep one worker failure from hiding other records
                record, task_error = _fallback_result(task, exc)
                task_errors = [task_error]
            file_records.append(record)
            error_rows.extend(_error_row(task, run_id, error) for error in task_errors)

    file_records.sort(key=lambda record: (record["source_root_id"], record["relative_path"]))
    error_rows.sort(
        key=lambda row: (
            row["source_root_id"],
            row["relative_path"],
            row["stage"],
            row["timestamp"],
        )
    )
    duplicate_rows = group_exact_duplicates(file_records)
    sample_manifest = _sample_manifest(
        stage,
        run_id,
        active_roots,
        discovered,
        sample,
        excluded_file_instance_ids,
        prior_run_id,
    )

    finished_at = _utc_now()
    wall_time_seconds = time.perf_counter() - started_clock
    total_bytes = sum(record["size_bytes"] or 0 for record in file_records)
    successful_files = sum(record["inventory_status"] == "success" for record in file_records)
    partial_files = sum(record["inventory_status"] == "partial" for record in file_records)
    failed_files = sum(record["inventory_status"] == "failed" for record in file_records)
    text_counts = {
        status: sum(record["text_layer_status"] == status for record in file_records)
        for status in ("text_present", "text_absent", "mixed_or_uncertain", "check_failed")
    }
    filename_counts = {
        status: sum(record["filename_parse_status"] == status for record in file_records)
        for status in ("matched", "unmatched", "error")
    }
    statistics = {
        "sampled_files": len(tasks),
        "processed_files": len(file_records),
        "successful_files": successful_files,
        "partial_files": partial_files,
        "failed_files": failed_files,
        "total_bytes": total_bytes,
        "wall_time_seconds": wall_time_seconds,
        "files_per_second": len(file_records) / wall_time_seconds if wall_time_seconds else 0.0,
        "mib_per_second": total_bytes / (1024 * 1024) / wall_time_seconds if wall_time_seconds else 0.0,
        "error_count": len(error_rows),
        "text_present_count": text_counts["text_present"],
        "text_absent_count": text_counts["text_absent"],
        "mixed_or_uncertain_count": text_counts["mixed_or_uncertain"],
        "text_check_failed_count": text_counts["check_failed"],
        "encrypted_count": sum(record["pdf_status"] == "encrypted" for record in file_records),
        "pdf_open_error_count": sum(record["pdf_open_status"] == "failed" for record in file_records),
        "exact_duplicate_group_count": len({row["duplicate_group_id"] for row in duplicate_rows}),
        "exact_duplicate_file_count": len(duplicate_rows),
        "filename_matched_count": filename_counts["matched"],
        "filename_unmatched_count": filename_counts["unmatched"],
    }
    manifest = {
        "inventory_run_id": run_id,
        "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
        "hostname": socket.gethostname(),
        "git_commit": git_commit,
        "dirty": dirty,
        "python_version": platform.python_version(),
        "tool_versions": _tool_versions(),
        "source_roots": [root.snapshot() for root in active_roots],
        "migb_data_root": str(config.migb_data_root),
        "config_snapshot": config.snapshot(),
        "started_at": started_at,
        "completed_at": finished_at,
        "discovered_count": len(discovered),
        "sampled_count": len(tasks),
        "processed_count": len(file_records),
        "success_count": successful_files,
        "partial_count": partial_files,
        "failure_count": failed_files,
        "source_safety_check": "passed",
        "worker_count": config.inventory.worker_count,
        "output_artifacts": list(ARTIFACT_NAMES),
    }
    if stage == "d2":
        manifest.update(
            {
                "sampling_stage": "d2",
                "target_sample_count": sample_manifest["target_sample_count"],
                "actual_sample_count": sample_manifest["actual_sample_count"],
                "target_per_group_count": sample_manifest["target_per_group_count"],
                "per_group_sample_count": sample_manifest["per_group_sample_count"],
                "excluded_prior_run_id": prior_run_id,
                "excluded_prior_sample_count": sample_manifest["excluded_prior_sample_count"],
                "excluded_prior_sample_found_count": sample_manifest[
                    "excluded_prior_sample_found_count"
                ],
                "excluded_prior_sample_missing_count": sample_manifest[
                    "excluded_prior_sample_missing_count"
                ],
            }
        )
    write_d1_artifacts(
        run_directory,
        file_records,
        duplicate_rows,
        error_rows,
        sample_manifest,
        manifest,
        statistics,
    )
    return D1RunResult(
        run_id=run_id,
        run_directory=run_directory,
        manifest=manifest,
        statistics=statistics,
    )


def run_d1(
    config: EnvironmentConfig,
    repo_root: str | Path = ".",
    run_id: str | None = None,
) -> D1RunResult:
    """Run D1 for the configured Source Roots and write all six Artifacts."""

    return _run_stage(config, "d1", repo_root=repo_root, run_id=run_id)


def run_d2(
    config: EnvironmentConfig,
    prior_run_id: str,
    repo_root: str | Path = ".",
    run_id: str | None = None,
) -> D1RunResult:
    """Run D2 while excluding File Instances recorded by a prior D1 run."""

    return _run_stage(
        config,
        "d2",
        repo_root=repo_root,
        run_id=run_id,
        prior_run_id=prior_run_id,
    )


@dataclass(frozen=True)
class D3RunResult:
    """Result for a D3 run, including a controlled interrupted run."""

    run_id: str
    run_directory: Path
    manifest: dict[str, Any]
    statistics: dict[str, Any]
    run_status: str


@dataclass(frozen=True)
class _TaskOutcome:
    record: dict[str, Any]
    errors: list[dict[str, str]]


def _validate_simple_run_id(run_id: str, prefix: str) -> None:
    if (
        not isinstance(run_id, str)
        or not run_id
        or Path(run_id).name != run_id
        or not run_id.startswith(prefix)
    ):
        raise PipelineError(f"run ID must be a simple {prefix} run ID")


def _read_json_mapping(path: Path, description: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"cannot read {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PipelineError(f"{description} {path} must contain a JSON object")
    return value


def _load_prior_sample_manifest(
    config: EnvironmentConfig,
    prior_run_id: str,
) -> tuple[set[str], int]:
    """Load and validate one complete prior D1/D2 sample manifest."""

    prefix = "d1-" if prior_run_id.startswith("d1-") else "d2-"
    _validate_simple_run_id(prior_run_id, prefix)
    manifest_path = (
        config.migb_data_root
        / "inventory"
        / "runs"
        / prior_run_id
        / "sample_manifest.json"
    )
    manifest = _read_json_mapping(manifest_path, "prior sample manifest")
    if manifest.get("inventory_run_id") != prior_run_id:
        raise PipelineError(
            f"prior sample manifest inventory_run_id does not match {prior_run_id}"
        )
    sampling_stage = manifest.get("sampling_stage")
    if prefix == "d1-" and sampling_stage not in (None, "d1"):
        raise PipelineError(f"prior D1 sample manifest has unexpected sampling_stage: {sampling_stage}")
    if prefix == "d2-" and sampling_stage != "d2":
        raise PipelineError("prior D2 sample manifest must have sampling_stage=d2")

    items = manifest.get("items")
    if not isinstance(items, list):
        raise PipelineError("prior sample manifest items must be a list")
    if manifest.get("sample_count") != len(items):
        raise PipelineError("prior sample manifest sample_count does not match items")
    if prefix == "d2-" and manifest.get("actual_sample_count") != len(items):
        raise PipelineError("prior D2 sample manifest actual_sample_count does not match items")

    excluded_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise PipelineError(f"prior sample manifest item {index} must be an object")
        source_root_id = item.get("source_root_id")
        relative_path = item.get("relative_path")
        item_id = item.get("file_instance_id")
        if not all(isinstance(value, str) for value in (source_root_id, relative_path, item_id)):
            raise PipelineError(f"prior sample manifest item {index} has incomplete identity fields")
        expected_id = file_instance_id(source_root_id, relative_path)
        if item_id != expected_id:
            raise PipelineError(
                f"prior sample manifest item {index} File Instance ID does not match its path"
            )
        if item_id in excluded_ids:
            raise PipelineError(f"prior sample manifest contains duplicate File Instance: {item_id}")
        excluded_ids.add(item_id)
    return excluded_ids, len(items)


def _load_d3_prior_exclusions(
    config: EnvironmentConfig,
    prior_run_ids: Sequence[str],
) -> tuple[set[str], dict[str, int]]:
    if isinstance(prior_run_ids, str):
        prior_run_ids = (prior_run_ids,)
    prior_run_ids = tuple(prior_run_ids)
    if len(prior_run_ids) < 2 or not any(run_id.startswith("d1-") for run_id in prior_run_ids):
        raise PipelineError("D3 requires validated D1 and D2 prior run IDs")
    if not any(run_id.startswith("d2-") for run_id in prior_run_ids):
        raise PipelineError("D3 requires a validated D2 prior run ID")
    if len(set(prior_run_ids)) != len(prior_run_ids):
        raise PipelineError("D3 prior run IDs must be unique")

    excluded_ids: set[str] = set()
    item_counts: dict[str, int] = {}
    for prior_run_id in prior_run_ids:
        ids, item_count = _load_prior_sample_manifest(config, prior_run_id)
        overlap = excluded_ids & ids
        if overlap:
            raise PipelineError(
                f"D3 prior sample manifests overlap on {len(overlap)} File Instances"
            )
        excluded_ids.update(ids)
        item_counts[prior_run_id] = item_count
    return excluded_ids, item_counts


def _d3_sample_manifest(
    run_id: str,
    active_roots: list[Any],
    sample: D3Sample,
    prior_run_ids: Sequence[str],
    prior_item_counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "inventory_run_id": run_id,
        "source_root_id": active_roots[0].source_root_id if len(active_roots) == 1 else None,
        "sampling_stage": "d3",
        "sampling_method": sample.sampling_method,
        "sample_count": len(sample.items),
        "target_sample_count": sample.target_sample_count,
        "actual_sample_count": sample.actual_sample_count,
        "excluded_prior_runs": list(prior_run_ids),
        "excluded_prior_item_count": sample.excluded_prior_item_count,
        "excluded_prior_item_counts": [
            {"run_id": run_id_value, "item_count": prior_item_counts[run_id_value]}
            for run_id_value in prior_run_ids
        ],
        "per_group": [
            {
                "source_root_id": quota.source_root_id,
                "parent_group": quota.parent_group,
                "remaining_population": quota.remaining_population,
                "base_quota": quota.base_quota,
                "proportional_quota": quota.proportional_quota,
                "largest_remainder_award": quota.largest_remainder_award,
                "final_quota": quota.final_quota,
            }
            for quota in sample.per_group
        ],
        "items": [
            {
                "source_root_id": item.source_root_id,
                "parent_group": item.parent_group,
                "file_instance_id": file_instance_id(item.source_root_id, item.relative_path),
                "relative_path": item.relative_path,
            }
            for item in sample.items
        ],
    }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _d3_config_fingerprint(
    config: EnvironmentConfig,
    prior_run_ids: Sequence[str],
    target_sample_count: int,
    base_quota: int,
) -> str:
    """Hash semantic D3 inputs while intentionally excluding worker_count."""

    tool_versions = _tool_versions()
    fingerprint_payload = {
        "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
        "source_roots": [root.snapshot() for root in config.source_roots if root.enabled],
        "sampling_stage": "d3",
        "sampling_method": "proportional_parent_group_evenly_spaced_v0.1",
        "target_sample_count": target_sample_count,
        "base_quota": base_quota,
        "excluded_prior_runs": list(prior_run_ids),
        "worker_independent_processing_settings": {
            "text_page_char_threshold": config.inventory.text_page_char_threshold,
            "pdf_library": "PyMuPDF",
            "pdf_library_version": tool_versions.get("PyMuPDF", "not_installed"),
        },
    }
    return _sha256_bytes(json_bytes(fingerprint_payload))


def _checkpoint_paths(run_directory: Path) -> tuple[Path, Path]:
    return run_directory / "checkpoints" / "files", run_directory / "checkpoints" / "errors"


def _write_d3_checkpoint(
    run_directory: Path,
    part_index: int,
    file_records: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
) -> None:
    files_directory, errors_directory = _checkpoint_paths(run_directory)
    files_directory.mkdir(parents=True, exist_ok=True)
    errors_directory.mkdir(parents=True, exist_ok=True)
    files_path = files_directory / f"part-{part_index:05d}.parquet"
    errors_path = errors_directory / f"part-{part_index:05d}.parquet"
    if files_path.exists() or errors_path.exists():
        raise PipelineError(f"checkpoint part already exists: {part_index:05d}")
    write_parquet_atomic(file_records, files_path, files_schema())
    write_parquet_atomic(error_rows, errors_path, errors_schema())


def _load_d3_checkpoints(
    run_directory: Path,
    run_id: str,
    sample_ids: set[str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    """Load complete checkpoint pairs and reject partial/corrupt state."""

    files_directory, errors_directory = _checkpoint_paths(run_directory)
    file_parts = sorted(files_directory.glob("part-*.parquet")) if files_directory.exists() else []
    error_parts = sorted(errors_directory.glob("part-*.parquet")) if errors_directory.exists() else []
    file_names = {path.name for path in file_parts}
    error_names = {path.name for path in error_parts}
    if file_names != error_names:
        raise PipelineError("checkpoint files/errors parts are incomplete")

    records: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for files_path, errors_path in zip(file_parts, error_parts):
        files_table = pq.read_table(files_path)
        errors_table = pq.read_table(errors_path)
        if not files_table.schema.equals(files_schema()):
            raise PipelineError(f"checkpoint files schema mismatch: {files_path}")
        if not errors_table.schema.equals(errors_schema()):
            raise PipelineError(f"checkpoint errors schema mismatch: {errors_path}")
        for record in files_table.to_pylist():
            item_id = record.get("file_instance_id")
            if item_id not in sample_ids:
                raise PipelineError("checkpoint contains a File Instance outside the D3 sample")
            if record.get("inventory_run_id") != run_id:
                raise PipelineError("checkpoint record has a mismatched inventory_run_id")
            if item_id in records:
                raise PipelineError(f"checkpoint contains duplicate File Instance: {item_id}")
            records[item_id] = record
        for error in errors_table.to_pylist():
            item_id = error.get("file_instance_id")
            if item_id not in sample_ids:
                raise PipelineError("checkpoint error contains a File Instance outside the D3 sample")
            if error.get("inventory_run_id") != run_id:
                raise PipelineError("checkpoint error has a mismatched inventory_run_id")
            errors.append(error)
    errors.sort(
        key=lambda row: (
            row["source_root_id"],
            row["relative_path"],
            row["stage"],
            row["timestamp"],
        )
    )
    return records, errors


def _write_d3_run_state(run_directory: Path, state: dict[str, Any]) -> None:
    write_json_atomic(state, run_directory / ".run_state.json")


def _read_d3_run_state(run_directory: Path) -> dict[str, Any]:
    return _read_json_mapping(run_directory / ".run_state.json", "D3 run state")


_RETRYABLE_ERROR_CATEGORIES = frozenset(
    {
        "OSError",
        "TimeoutError",
        "ConnectionError",
        "BlockingIOError",
        "InterruptedError",
        "FileNotFoundError",
        "PermissionError",
    }
)
_RETRYABLE_ERROR_STAGES = frozenset(
    {"stat_before", "hash", "pdf_open", "metadata", "worker"}
)


def _is_retryable_error(error: dict[str, str]) -> bool:
    return (
        error.get("stage") in _RETRYABLE_ERROR_STAGES
        and error.get("error_category") in _RETRYABLE_ERROR_CATEGORIES
    )


def _run_one_process_attempt(
    tasks: list[dict[str, Any]],
    worker_count: int,
) -> dict[str, _TaskOutcome]:
    outcomes: dict[str, _TaskOutcome] = {}
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        future_to_task = {executor.submit(process_file_task, task): task for task in tasks}
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                record, task_errors = future.result()
            except Exception as exc:  # keep one worker failure from hiding other records
                record, task_error = _fallback_result(task, exc)
                task_errors = [task_error]
            outcomes[task["file_instance_id"]] = _TaskOutcome(record, task_errors)
    return outcomes


def _run_tasks_with_retries_detailed(
    tasks: list[dict[str, Any]],
    worker_count: int,
) -> tuple[dict[str, _TaskOutcome], int, int, int]:
    """Run a batch with bounded retries and report exhausted retry tasks."""

    pending = {task["file_instance_id"]: task for task in tasks}
    final: dict[str, _TaskOutcome] = {}
    retry_attempts_total = 0
    recovered_by_retry = 0
    retry_exhausted_count = 0
    for attempt in range(D3_MAX_RETRIES + 1):
        if not pending:
            break
        attempt_outcomes = _run_one_process_attempt(list(pending.values()), worker_count)
        retry_tasks: dict[str, dict[str, Any]] = {}
        for item_id, outcome in attempt_outcomes.items():
            if (
                outcome.errors
                and all(_is_retryable_error(error) for error in outcome.errors)
                and attempt < D3_MAX_RETRIES
            ):
                retry_tasks[item_id] = pending[item_id]
            else:
                if (
                    attempt == D3_MAX_RETRIES
                    and outcome.errors
                    and all(_is_retryable_error(error) for error in outcome.errors)
                ):
                    retry_exhausted_count += 1
                if attempt > 0 and not outcome.errors:
                    recovered_by_retry += 1
                final[item_id] = outcome
        if not retry_tasks:
            break
        retry_attempts_total += len(retry_tasks)
        time.sleep(D3_RETRY_BACKOFF_SECONDS[attempt])
        pending = retry_tasks
    return final, retry_attempts_total, recovered_by_retry, retry_exhausted_count


def _run_tasks_with_retries(
    tasks: list[dict[str, Any]],
    worker_count: int,
) -> tuple[dict[str, _TaskOutcome], int, int]:
    """Run a task batch with at most two bounded retries for transient I/O errors."""

    outcomes, retry_attempts, recovered, _ = _run_tasks_with_retries_detailed(
        tasks,
        worker_count,
    )
    return outcomes, retry_attempts, recovered


def _chunks(values: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _d3_statistics(
    file_records: list[dict[str, Any]],
    error_rows: list[dict[str, str]],
    *,
    sampled_count: int,
    run_status: str,
    wall_time_seconds: float,
    checkpoint_write_time_seconds: float,
    resume_startup_time_seconds: float,
    resume_count: int,
    checkpoint_reused_count: int,
    checkpoint_reprocessed_count: int,
    retry_attempts_total: int,
    files_recovered_by_retry: int,
) -> dict[str, Any]:
    text_counts = {
        status: sum(record["text_layer_status"] == status for record in file_records)
        for status in ("text_present", "text_absent", "mixed_or_uncertain", "check_failed")
    }
    filename_counts = {
        status: sum(record["filename_parse_status"] == status for record in file_records)
        for status in ("matched", "unmatched", "error")
    }
    return {
        "run_status": run_status,
        "sampled_files": sampled_count,
        "processed_files": len(file_records),
        "successful_files": sum(record["inventory_status"] == "success" for record in file_records),
        "partial_files": sum(record["inventory_status"] == "partial" for record in file_records),
        "failed_files": sum(record["inventory_status"] == "failed" for record in file_records),
        "total_bytes": sum(record["size_bytes"] or 0 for record in file_records),
        "wall_time_seconds": wall_time_seconds,
        "files_per_second": len(file_records) / wall_time_seconds if wall_time_seconds else 0.0,
        "mib_per_second": (
            sum(record["size_bytes"] or 0 for record in file_records) / (1024 * 1024) / wall_time_seconds
            if wall_time_seconds
            else 0.0
        ),
        "error_count": len(error_rows),
        "text_present_count": text_counts["text_present"],
        "text_absent_count": text_counts["text_absent"],
        "mixed_or_uncertain_count": text_counts["mixed_or_uncertain"],
        "text_check_failed_count": text_counts["check_failed"],
        "zero_page_count": sum(
            error["error_category"] == "zero_page_count" for error in error_rows
        ),
        "encrypted_count": sum(record["pdf_status"] == "encrypted" for record in file_records),
        "pdf_open_error_count": sum(record["pdf_open_status"] == "failed" for record in file_records),
        "exact_duplicate_group_count": len(
            {row["duplicate_group_id"] for row in group_exact_duplicates(file_records)}
        ),
        "exact_duplicate_file_count": len(group_exact_duplicates(file_records)),
        "filename_matched_count": filename_counts["matched"],
        "filename_unmatched_count": filename_counts["unmatched"],
        "filename_error_count": filename_counts["error"],
        "checkpoint_write_time_seconds": checkpoint_write_time_seconds,
        "resume_startup_time_seconds": resume_startup_time_seconds,
        "resume_count": resume_count,
        "checkpoint_reused_count": checkpoint_reused_count,
        "checkpoint_reprocessed_count": checkpoint_reprocessed_count,
        "retry_attempts_total": retry_attempts_total,
        "files_recovered_by_retry": files_recovered_by_retry,
    }


def _write_d3_manifest_with_checksums(
    run_directory: Path,
    manifest: dict[str, Any],
) -> None:
    """Write a D3 manifest with checksums for all six canonical artifacts.

    A file cannot contain the raw SHA-256 of its own final bytes.  The manifest
    descriptor therefore records the SHA-256 of a normalized manifest in which
    its own checksum value is replaced with 64 zeroes; the basis is explicit in
    the descriptor for independent verification.
    """

    descriptors_by_name: dict[str, dict[str, Any]] = {}
    for artifact_name in ARTIFACT_NAMES:
        if artifact_name == "manifest.json":
            continue
        descriptors_by_name[artifact_name] = artifact_descriptor(
            run_directory / artifact_name
        )
    checksum_basis = "manifest.json with its own sha256 normalized to 64 zeroes"
    self_descriptor: dict[str, Any] = {
        "path": "manifest.json",
        "size_bytes": 0,
        "sha256": "0" * 64,
        "checksum_basis": checksum_basis,
    }
    manifest["output_artifacts"] = [
        self_descriptor if artifact_name == "manifest.json" else descriptors_by_name[artifact_name]
        for artifact_name in ARTIFACT_NAMES
    ]

    size_guess = 0
    for _ in range(10):
        self_descriptor["size_bytes"] = size_guess
        size_value = len(json_bytes(manifest))
        if size_value == size_guess:
            break
        size_guess = size_value
    else:  # pragma: no cover - JSON size converges immediately
        raise PipelineError("could not stabilize manifest checksum size")

    self_descriptor["size_bytes"] = size_guess
    normalized_manifest = json_bytes(manifest)
    self_descriptor["sha256"] = _sha256_bytes(normalized_manifest)
    final_manifest = json_bytes(manifest)
    if len(final_manifest) != size_guess:  # pragma: no cover - digest length is fixed
        raise PipelineError("manifest checksum size changed unexpectedly")
    write_json_atomic(manifest, run_directory / "manifest.json")


def _d3_interrupted_result(
    run_directory: Path,
    run_id: str,
    sample_manifest: dict[str, Any],
    state: dict[str, Any],
    statistics: dict[str, Any],
) -> D3RunResult:
    manifest = {
        "inventory_run_id": run_id,
        "run_status": state["run_status"],
        "sampling_stage": "d3",
        "sampling_method": sample_manifest["sampling_method"],
        "target_sample_count": sample_manifest["target_sample_count"],
        "actual_sample_count": sample_manifest["actual_sample_count"],
        "processed_count": state["completed_count"],
        "git_commit": state["git_commit"],
        "config_fingerprint": state["config_fingerprint"],
        "sample_manifest_hash": state["sample_manifest_hash"],
        "resume_count": state["resume_count"],
        "checkpoint_reused_count": state["checkpoint_reused_count"],
        "checkpoint_reprocessed_count": state["checkpoint_reprocessed_count"],
    }
    return D3RunResult(
        run_id=run_id,
        run_directory=run_directory,
        manifest=manifest,
        statistics=statistics,
        run_status=state["run_status"],
    )


def run_d3(
    config: EnvironmentConfig,
    prior_run_ids: Sequence[str],
    repo_root: str | Path = ".",
    run_id: str | None = None,
    *,
    resume: bool = False,
    target_sample_count: int = D3_TARGET_SAMPLE_COUNT,
    base_quota: int = 5,
    checkpoint_batch_size: int = D3_CHECKPOINT_BATCH_SIZE,
    stop_after: int | None = None,
) -> D3RunResult:
    """Run or resume the D3 1000-file scale test with durable checkpoints."""

    if isinstance(target_sample_count, bool) or target_sample_count < 1:
        raise PipelineError("D3 target_sample_count must be positive")
    if isinstance(checkpoint_batch_size, bool) or checkpoint_batch_size < 1:
        raise PipelineError("D3 checkpoint_batch_size must be positive")
    if stop_after is not None and (isinstance(stop_after, bool) or stop_after < 1):
        raise PipelineError("D3 stop_after must be positive when provided")
    if resume and not run_id:
        raise PipelineError("D3 resume requires an existing run_id")
    if run_id is not None:
        _validate_simple_run_id(run_id, "d3-")

    active_roots, output_root = _active_roots_and_safe_output(config)
    if isinstance(prior_run_ids, str):
        prior_run_ids = (prior_run_ids,)
    else:
        prior_run_ids = tuple(prior_run_ids)
    prior_excluded_ids, prior_item_counts = _load_d3_prior_exclusions(config, prior_run_ids)
    started_clock = time.perf_counter()
    repo_root = Path(repo_root).resolve()
    git_commit, dirty = _git_provenance(repo_root)
    if run_id is None:
        git_suffix = git_commit[:7] if git_commit != "unknown" else "unknown"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"d3-{timestamp}-{git_suffix}"

    discovered = _discover_active_roots(active_roots)
    sample = select_d3(
        discovered,
        prior_excluded_ids,
        target_sample_count=target_sample_count,
        base_quota=base_quota,
    )
    tasks = [
        _task_for(item, config.inventory.text_page_char_threshold, run_id)
        for item in sample.items
    ]
    sample_manifest = _d3_sample_manifest(
        run_id,
        active_roots,
        sample,
        prior_run_ids,
        prior_item_counts,
    )
    sample_manifest_hash = _sha256_bytes(json_bytes(sample_manifest))
    config_fingerprint = _d3_config_fingerprint(
        config,
        prior_run_ids,
        target_sample_count,
        base_quota,
    )
    sample_ids = {
        item["file_instance_id"] for item in sample_manifest["items"]
    }
    run_directory = output_root / "inventory" / "runs" / run_id
    resume_startup_time_seconds = 0.0

    if resume:
        if not run_directory.is_dir():
            raise PipelineError(f"D3 run directory does not exist: {run_directory}")
        state = _read_d3_run_state(run_directory)
        if state.get("inventory_run_id") != run_id:
            raise PipelineError("D3 run state inventory_run_id does not match run_id")
        if state.get("run_status") == "completed":
            raise PipelineError("a completed D3 run is immutable and cannot be resumed")
        if state.get("run_status") not in D3_RUN_STATES - {"completed"}:
            raise PipelineError(f"unsupported D3 run state: {state.get('run_status')}")
        if state.get("inventory_schema_version") != INVENTORY_SCHEMA_VERSION:
            raise PipelineError("D3 run state schema version does not match")
        if state.get("git_commit") != git_commit:
            raise PipelineError("D3 resume requires the same Git commit")
        if state.get("config_fingerprint") != config_fingerprint:
            raise PipelineError("D3 resume rejected: configuration fingerprint changed")
        if state.get("sample_manifest_hash") != sample_manifest_hash:
            raise PipelineError("D3 resume rejected: sample manifest changed")
        if state.get("checkpoint_batch_size") != checkpoint_batch_size:
            raise PipelineError("D3 resume requires the same checkpoint_batch_size")
        if state.get("target_count") != len(tasks):
            raise PipelineError("D3 resume rejected: target count changed")
        sample_path = run_directory / "sample_manifest.json"
        if not sample_path.is_file() or _sha256_bytes(sample_path.read_bytes()) != sample_manifest_hash:
            raise PipelineError("D3 resume rejected: persisted sample_manifest.json changed")
        unexpected_canonical = [
            name
            for name in ARTIFACT_NAMES
            if name != "sample_manifest.json" and (run_directory / name).exists()
        ]
        if unexpected_canonical:
            raise PipelineError(
                "D3 active run contains canonical artifacts and cannot be safely resumed: "
                + ", ".join(unexpected_canonical)
            )
        checkpoint_records, checkpoint_errors = _load_d3_checkpoints(
            run_directory,
            run_id,
            sample_ids,
        )
        resume_startup_time_seconds = time.perf_counter() - started_clock
        state["resume_count"] += 1
        state["run_status"] = "running"
        state["updated_at"] = _utc_now()
        state["resume_startup_time_seconds"] = resume_startup_time_seconds
        _write_d3_run_state(run_directory, state)
    else:
        run_directory = create_run_directory(output_root, run_id)
        write_json_atomic(sample_manifest, run_directory / "sample_manifest.json")
        state = {
            "inventory_run_id": run_id,
            "run_status": "running",
            "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
            "git_commit": git_commit,
            "config_fingerprint": config_fingerprint,
            "sample_manifest_hash": sample_manifest_hash,
            "started_at": _utc_now(),
            "updated_at": _utc_now(),
            "target_count": len(tasks),
            "requested_target_count": target_sample_count,
            "completed_count": 0,
            "checkpoint_batch_size": checkpoint_batch_size,
            "resume_count": 0,
            "checkpoint_reused_count": 0,
            "checkpoint_reprocessed_count": 0,
            "retry_attempts_total": 0,
            "files_recovered_by_retry": 0,
            "checkpoint_write_time_seconds": 0.0,
            "resume_startup_time_seconds": 0.0,
        }
        _write_d3_run_state(run_directory, state)
        checkpoint_records = {}
        checkpoint_errors = []

    task_by_id = {task["file_instance_id"]: task for task in tasks}
    if set(checkpoint_records) - set(task_by_id):
        raise PipelineError("checkpoint contains an unknown D3 task")
    file_records: dict[str, dict[str, Any]] = {}
    error_rows: list[dict[str, str]] = []
    pending_tasks: list[dict[str, Any]] = []
    checkpoint_errors_by_id: dict[str, list[dict[str, str]]] = {}
    for error in checkpoint_errors:
        checkpoint_errors_by_id.setdefault(error["file_instance_id"], []).append(error)

    for task in tasks:
        item_id = task["file_instance_id"]
        checkpoint_record = checkpoint_records.get(item_id)
        if checkpoint_record is None:
            pending_tasks.append(task)
            continue
        try:
            current_stat = Path(task["path"]).stat()
        except OSError:
            current_stat = None
        if (
            current_stat is not None
            and checkpoint_record.get("size_bytes") == current_stat.st_size
            and checkpoint_record.get("mtime_ns") == current_stat.st_mtime_ns
        ):
            file_records[item_id] = checkpoint_record
            error_rows.extend(checkpoint_errors_by_id.get(item_id, []))
        else:
            pending_tasks.append(task)

    state["checkpoint_reused_count"] += len(file_records)
    reprocessed_from_checkpoint = len(checkpoint_records) - len(file_records)
    state["checkpoint_reprocessed_count"] += reprocessed_from_checkpoint
    if reprocessed_from_checkpoint:
        for item_id, checkpoint_record in checkpoint_records.items():
            if item_id in file_records:
                continue
            task = task_by_id[item_id]
            error_rows.append(
                _error_row(
                    task,
                    run_id,
                    {
                        "stage": "resume_consistency",
                        "error_category": "source_changed_since_checkpoint",
                        "error_message": (
                            "size or mtime differed from checkpoint; File Instance was reprocessed"
                        ),
                        "timestamp": _utc_now(),
                    },
                )
            )

    next_part_index = 0
    files_directory, _ = _checkpoint_paths(run_directory)
    if files_directory.exists():
        existing_parts = sorted(files_directory.glob("part-*.parquet"))
        if existing_parts:
            next_part_index = max(
                int(path.stem.split("-")[-1]) for path in existing_parts
            ) + 1

    try:
        for task_batch in _chunks(pending_tasks, checkpoint_batch_size):
            outcomes, retry_attempts, recovered = _run_tasks_with_retries(
                task_batch,
                config.inventory.worker_count,
            )
            state["retry_attempts_total"] += retry_attempts
            state["files_recovered_by_retry"] += recovered
            batch_records = [outcomes[task["file_instance_id"]].record for task in task_batch]
            batch_error_rows = list(error_rows)
            for task in task_batch:
                outcome = outcomes[task["file_instance_id"]]
                batch_error_rows.extend(
                    _error_row(task, run_id, error) for error in outcome.errors
                )
            batch_records.sort(key=lambda record: (record["source_root_id"], record["relative_path"]))
            new_errors = batch_error_rows[len(error_rows) :]
            new_errors.sort(
                key=lambda row: (
                    row["source_root_id"],
                    row["relative_path"],
                    row["stage"],
                    row["timestamp"],
                )
            )
            checkpoint_started = time.perf_counter()
            _write_d3_checkpoint(run_directory, next_part_index, batch_records, new_errors)
            state["checkpoint_write_time_seconds"] += time.perf_counter() - checkpoint_started
            next_part_index += 1
            for record in batch_records:
                file_records[record["file_instance_id"]] = record
            error_rows.extend(new_errors)
            error_rows.sort(
                key=lambda row: (
                    row["source_root_id"],
                    row["relative_path"],
                    row["stage"],
                    row["timestamp"],
                )
            )
            state["completed_count"] = len(file_records)
            state["updated_at"] = _utc_now()
            state["checkpoint_count"] = next_part_index
            _write_d3_run_state(run_directory, state)
            if stop_after is not None and len(file_records) >= stop_after and len(file_records) < len(tasks):
                state["run_status"] = "interrupted"
                state["updated_at"] = _utc_now()
                _write_d3_run_state(run_directory, state)
                interrupted_statistics = _d3_statistics(
                    sorted(file_records.values(), key=lambda record: (record["source_root_id"], record["relative_path"])),
                    error_rows,
                    sampled_count=len(tasks),
                    run_status="interrupted",
                    wall_time_seconds=time.perf_counter() - started_clock,
                    checkpoint_write_time_seconds=state["checkpoint_write_time_seconds"],
                    resume_startup_time_seconds=resume_startup_time_seconds,
                    resume_count=state["resume_count"],
                    checkpoint_reused_count=state["checkpoint_reused_count"],
                    checkpoint_reprocessed_count=state["checkpoint_reprocessed_count"],
                    retry_attempts_total=state["retry_attempts_total"],
                    files_recovered_by_retry=state["files_recovered_by_retry"],
                )
                return _d3_interrupted_result(
                    run_directory,
                    run_id,
                    sample_manifest,
                    state,
                    interrupted_statistics,
                )
    except Exception:
        state["run_status"] = "failed"
        state["completed_count"] = len(file_records)
        state["updated_at"] = _utc_now()
        _write_d3_run_state(run_directory, state)
        raise

    file_records_list = sorted(
        file_records.values(),
        key=lambda record: (record["source_root_id"], record["relative_path"]),
    )
    error_rows.sort(
        key=lambda row: (
            row["source_root_id"],
            row["relative_path"],
            row["stage"],
            row["timestamp"],
        )
    )
    duplicate_rows = group_exact_duplicates(file_records_list)
    finished_at = _utc_now()
    wall_time_seconds = time.perf_counter() - started_clock
    statistics = _d3_statistics(
        file_records_list,
        error_rows,
        sampled_count=len(tasks),
        run_status="completed",
        wall_time_seconds=wall_time_seconds,
        checkpoint_write_time_seconds=state["checkpoint_write_time_seconds"],
        resume_startup_time_seconds=resume_startup_time_seconds,
        resume_count=state["resume_count"],
        checkpoint_reused_count=state["checkpoint_reused_count"],
        checkpoint_reprocessed_count=state["checkpoint_reprocessed_count"],
        retry_attempts_total=state["retry_attempts_total"],
        files_recovered_by_retry=state["files_recovered_by_retry"],
    )
    manifest = {
        "inventory_run_id": run_id,
        "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
        "run_status": "completed",
        "hostname": socket.gethostname(),
        "git_commit": git_commit,
        "dirty": dirty,
        "python_version": platform.python_version(),
        "tool_versions": _tool_versions(),
        "source_roots": [root.snapshot() for root in active_roots],
        "migb_data_root": str(config.migb_data_root),
        "config_snapshot": config.snapshot(),
        "config_fingerprint": config_fingerprint,
        "sample_manifest_hash": sample_manifest_hash,
        "started_at": state["started_at"],
        "completed_at": finished_at,
        "discovered_count": len(discovered),
        "sampled_count": len(tasks),
        "processed_count": len(file_records_list),
        "success_count": statistics["successful_files"],
        "partial_count": statistics["partial_files"],
        "failure_count": statistics["failed_files"],
        "source_safety_check": "passed",
        "worker_count": config.inventory.worker_count,
        "sampling_stage": "d3",
        "sampling_method": sample.sampling_method,
        "target_sample_count": sample.target_sample_count,
        "actual_sample_count": sample.actual_sample_count,
        "excluded_prior_runs": list(prior_run_ids),
        "excluded_prior_item_count": len(prior_excluded_ids),
        "per_group": sample_manifest["per_group"],
        "resume_count": state["resume_count"],
        "checkpoint_reused_count": state["checkpoint_reused_count"],
        "checkpoint_reprocessed_count": state["checkpoint_reprocessed_count"],
        "retry_attempts_total": state["retry_attempts_total"],
        "files_recovered_by_retry": state["files_recovered_by_retry"],
        "output_artifacts": [],
    }

    # Canonical Parquet files are written only after all unique File Instances
    # have been accounted for.  An active run may leave only checkpoint parts.
    for artifact_name in ARTIFACT_NAMES:
        if artifact_name != "sample_manifest.json" and (run_directory / artifact_name).exists():
            raise PipelineError(f"canonical artifact already exists: {artifact_name}")
    write_parquet(file_records_list, run_directory / "files.parquet", files_schema())
    write_parquet(
        duplicate_rows,
        run_directory / "duplicate_groups.parquet",
        duplicate_groups_schema(),
    )
    write_parquet(error_rows, run_directory / "errors.parquet", errors_schema())
    write_json_atomic(statistics, run_directory / "statistics.json")
    _write_d3_manifest_with_checksums(run_directory, manifest)

    state["run_status"] = "completed"
    state["completed_count"] = len(file_records_list)
    state["updated_at"] = _utc_now()
    state["checkpoint_count"] = next_part_index
    _write_d3_run_state(run_directory, state)
    return D3RunResult(
        run_id=run_id,
        run_directory=run_directory,
        manifest=manifest,
        statistics=statistics,
        run_status="completed",
    )


@dataclass(frozen=True)
class FullRunResult:
    """Result for a complete, independently auditable Full Inventory run."""

    run_id: str
    run_directory: Path
    manifest: dict[str, Any]
    statistics: dict[str, Any]
    run_status: str
    artifact_validation: dict[str, Any]


def _proc_memory_and_swap() -> dict[str, Any]:
    """Read Linux memory/swap counters without adding a runtime dependency."""

    values: dict[str, int] = {}
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        try:
            for line in meminfo.read_text(encoding="utf-8").splitlines():
                key, separator, value = line.partition(":")
                if not separator:
                    continue
                parts = value.strip().split()
                if not parts:
                    continue
                try:
                    number = int(parts[0])
                except ValueError:
                    continue
                values[key] = number * 1024 if len(parts) > 1 and parts[1] == "kB" else number
        except OSError:
            values = {}

    swap_total = values.get("SwapTotal")
    swap_free = values.get("SwapFree")
    if swap_total is None:
        swap_status = "unavailable"
    elif swap_total == 0:
        swap_status = "disabled"
    else:
        swap_status = "enabled"
    return {
        "available_memory_bytes": values.get("MemAvailable"),
        "swap_status": swap_status,
        "swap_total_bytes": swap_total,
        "swap_free_bytes": swap_free,
    }


def _runtime_snapshot(
    output_root: Path,
    worker_count: int,
    checkpoint_batch_size: int,
) -> dict[str, Any]:
    """Capture the runtime values required by the Full Job Manifest."""

    disk_path = output_root if output_root.exists() else output_root.parent
    try:
        disk_usage = shutil.disk_usage(disk_path)
        disk_total_bytes: int | None = disk_usage.total
        disk_available_bytes: int | None = disk_usage.free
    except OSError:
        disk_total_bytes = None
        disk_available_bytes = None

    uptime_seconds: float | None = None
    uptime_path = Path("/proc/uptime")
    if uptime_path.is_file():
        try:
            uptime_seconds = float(uptime_path.read_text(encoding="utf-8").split()[0])
        except (OSError, IndexError, ValueError):
            uptime_seconds = None

    return {
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
        "tool_versions": _tool_versions(),
        "worker_count": worker_count,
        "checkpoint_batch_size": checkpoint_batch_size,
        "disk_path": str(disk_path),
        "disk_total_bytes": disk_total_bytes,
        "disk_available_bytes": disk_available_bytes,
        "uptime_seconds": uptime_seconds,
        **_proc_memory_and_swap(),
    }


def _full_sample_manifest(
    run_id: str,
    active_roots: list[Any],
    discovered: list[DiscoveredFile],
    target_count: int,
) -> dict[str, Any]:
    ordered = sorted(
        discovered,
        key=lambda item: (item.source_root_id, item.relative_path),
    )
    items = [
        {
            "source_root_id": item.source_root_id,
            "parent_group": item.parent_group,
            "file_instance_id": file_instance_id(item.source_root_id, item.relative_path),
            "relative_path": item.relative_path,
        }
        for item in ordered
    ]
    actual_count = len(items)
    return {
        "inventory_run_id": run_id,
        "inventory_schema_version": FULL_INVENTORY_SCHEMA_VERSION,
        "selection_stage": "full",
        "sampling_stage": "full",
        "selection_method": FULL_SELECTION_METHOD,
        "sampling_method": FULL_SELECTION_METHOD,
        "source_root_id": active_roots[0].source_root_id if len(active_roots) == 1 else None,
        "target_count": target_count,
        "actual_count": actual_count,
        "selected_count": actual_count,
        "sample_count": actual_count,
        "items": items,
    }


def _full_config_fingerprint(
    config: EnvironmentConfig,
    *,
    expected_pdf_count: int | None,
    expected_top_level_group_count: int | None,
    checkpoint_batch_size: int,
) -> str:
    """Hash Full semantic inputs used by resume validation."""

    fingerprint_payload = {
        "inventory_schema_version": FULL_INVENTORY_SCHEMA_VERSION,
        "source_roots": [
            root.snapshot() for root in config.source_roots if root.enabled
        ],
        "selection_stage": "full",
        "selection_method": FULL_SELECTION_METHOD,
        "expected_pdf_count": expected_pdf_count,
        "expected_top_level_group_count": expected_top_level_group_count,
        "worker_count": config.inventory.worker_count,
        "checkpoint_batch_size": checkpoint_batch_size,
        "max_retries": D3_MAX_RETRIES,
        "retry_backoff_seconds": list(D3_RETRY_BACKOFF_SECONDS),
        "processing_settings": {
            "text_page_char_threshold": config.inventory.text_page_char_threshold,
            "pdf_library": "PyMuPDF",
            "pdf_library_version": _tool_versions().get("PyMuPDF", "not_installed"),
            "classify_zero_page_as_invalid": True,
        },
    }
    return _sha256_bytes(json_bytes(fingerprint_payload))


def _write_full_checkpoint(
    run_directory: Path,
    part_index: int,
    file_records: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
) -> None:
    files_directory, errors_directory = _checkpoint_paths(run_directory)
    files_directory.mkdir(parents=True, exist_ok=True)
    errors_directory.mkdir(parents=True, exist_ok=True)
    files_path = files_directory / f"part-{part_index:05d}.parquet"
    errors_path = errors_directory / f"part-{part_index:05d}.parquet"
    if files_path.exists() or errors_path.exists():
        raise PipelineError(f"Full checkpoint part already exists: {part_index:05d}")
    write_parquet_atomic(file_records, files_path, files_schema())
    write_parquet_atomic(error_rows, errors_path, errors_schema())


def _load_full_checkpoints(
    run_directory: Path,
    run_id: str,
    selected_ids: set[str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    """Load complete Full checkpoint pairs and enforce Full schema/version."""

    files_directory, errors_directory = _checkpoint_paths(run_directory)
    file_parts = (
        sorted(files_directory.glob("part-*.parquet"))
        if files_directory.exists()
        else []
    )
    error_parts = (
        sorted(errors_directory.glob("part-*.parquet"))
        if errors_directory.exists()
        else []
    )
    if {path.name for path in file_parts} != {path.name for path in error_parts}:
        raise PipelineError("Full checkpoint files/errors parts are incomplete")

    records: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for files_path, errors_path in zip(file_parts, error_parts):
        files_table = pq.read_table(files_path)
        errors_table = pq.read_table(errors_path)
        if not files_table.schema.equals(files_schema()):
            raise PipelineError(f"Full checkpoint files schema mismatch: {files_path}")
        if not errors_table.schema.equals(errors_schema()):
            raise PipelineError(f"Full checkpoint errors schema mismatch: {errors_path}")
        for record in files_table.to_pylist():
            item_id = record.get("file_instance_id")
            if item_id not in selected_ids:
                raise PipelineError("Full checkpoint contains an unknown File Instance")
            if record.get("inventory_run_id") != run_id:
                raise PipelineError("Full checkpoint record has a mismatched inventory_run_id")
            if record.get("inventory_schema_version") != FULL_INVENTORY_SCHEMA_VERSION:
                raise PipelineError("Full checkpoint record has an incompatible schema version")
            if item_id in records:
                raise PipelineError(f"Full checkpoint contains duplicate File Instance: {item_id}")
            records[item_id] = record
        for error in errors_table.to_pylist():
            item_id = error.get("file_instance_id")
            if item_id not in selected_ids:
                raise PipelineError("Full checkpoint error contains an unknown File Instance")
            if error.get("inventory_run_id") != run_id:
                raise PipelineError("Full checkpoint error has a mismatched inventory_run_id")
            errors.append(error)
    errors.sort(
        key=lambda row: (
            row["source_root_id"],
            row["relative_path"],
            row["stage"],
            row["timestamp"],
        )
    )
    return records, errors


def _write_full_run_state(run_directory: Path, state: dict[str, Any]) -> None:
    write_json_atomic(state, run_directory / ".run_state.json")


def _read_full_run_state(run_directory: Path) -> dict[str, Any]:
    return _read_json_mapping(run_directory / ".run_state.json", "Full run state")


def _full_prior_artifact_integrity(
    config: EnvironmentConfig,
    prior_run_ids: Sequence[str] | None,
) -> dict[str, Any]:
    """Capture raw SHA-256 values for immutable D1/D2/D3 Canonical Artifacts."""

    run_ids = tuple(prior_run_ids or ())
    if len(set(run_ids)) != len(run_ids):
        raise PipelineError("Full prior run IDs must be unique")
    runs: list[dict[str, Any]] = []
    for prior_run_id in run_ids:
        if prior_run_id.startswith("d1-"):
            prefix = "d1-"
        elif prior_run_id.startswith("d2-"):
            prefix = "d2-"
        elif prior_run_id.startswith("d3-"):
            prefix = "d3-"
        else:
            raise PipelineError("Full prior run IDs must be D1, D2 or D3 run IDs")
        _validate_simple_run_id(prior_run_id, prefix)
        run_directory = (
            config.migb_data_root / "inventory" / "runs" / prior_run_id
        )
        manifest = _read_json_mapping(run_directory / "manifest.json", "prior run manifest")
        if manifest.get("inventory_run_id") != prior_run_id:
            raise PipelineError(f"prior run manifest inventory_run_id mismatch: {prior_run_id}")
        artifacts: list[dict[str, Any]] = []
        for artifact_name in ARTIFACT_NAMES:
            artifact_path = run_directory / artifact_name
            if not artifact_path.is_file():
                raise PipelineError(
                    f"prior run {prior_run_id} is missing Canonical Artifact {artifact_name}"
                )
            artifacts.append(artifact_descriptor(artifact_path))
        runs.append({"run_id": prior_run_id, "artifacts": artifacts})
    return {
        "status": "captured" if runs else "not_requested",
        "runs": runs,
    }


def _prior_integrity_matches(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return before == after


def _full_preflight_gate(
    snapshot: SourceSnapshot,
    *,
    expected_pdf_count: int | None,
    expected_top_level_group_count: int | None,
    prior_snapshot: SourceSnapshot | None = None,
) -> None:
    count_matches = (
        expected_pdf_count is None or snapshot.discovered_count == expected_pdf_count
    )
    group_matches = (
        expected_top_level_group_count is None
        or snapshot.top_level_group_count == expected_top_level_group_count
    )
    if count_matches and group_matches:
        return

    if prior_snapshot is not None:
        diff = compare_source_snapshots(prior_snapshot, snapshot)
        added_paths: Any = diff["added_examples"]
        missing_paths: Any = diff["missing_examples"]
        baseline_note = "compared with the latest prior Full source snapshot"
    else:
        added_paths = []
        missing_paths = []
        baseline_note = "no prior path-level source snapshot is available"
    raise PipelineError(
        "Full preflight count/group gate failed: "
        f"expected_count={expected_pdf_count} actual_count={snapshot.discovered_count}; "
        f"expected_top_level_group_count={expected_top_level_group_count} "
        f"actual_top_level_group_count={snapshot.top_level_group_count}; "
        f"added_paths={json.dumps(added_paths, ensure_ascii=False)}; "
        f"missing_paths={json.dumps(missing_paths, ensure_ascii=False)}; {baseline_note}."
    )


def _latest_full_source_snapshot(
    output_root: Path,
    active_roots: list[Any],
) -> SourceSnapshot | None:
    """Load a prior Full path snapshot when one exists for the same roots."""

    runs_directory = output_root / "inventory" / "runs"
    if not runs_directory.is_dir():
        return None
    expected_root_ids = tuple(sorted(root.source_root_id for root in active_roots))
    for run_directory in sorted(runs_directory.glob("full-*/"), reverse=True):
        snapshot_path = run_directory / "source_snapshot_before.json"
        if not snapshot_path.is_file():
            continue
        try:
            snapshot = SourceSnapshot.from_dict(
                _read_json_mapping(snapshot_path, "prior Full source snapshot")
            )
        except (PipelineError, ValueError, OSError, json.JSONDecodeError):
            continue
        root_ids = tuple(
            sorted(str(root.get("source_root_id")) for root in snapshot.source_roots)
        )
        if root_ids == expected_root_ids:
            return snapshot
    return None


def _distribution(values: list[int]) -> dict[str, Any]:
    """Return deterministic min/median/p90/p95/p99/max statistics."""

    if not values:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "max": None,
        }
    ordered = sorted(values)

    def percentile(fraction: float) -> int | float:
        position = (len(ordered) - 1) * fraction
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return ordered[lower]
        value = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
        return int(value) if float(value).is_integer() else value

    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": percentile(0.50),
        "p90": percentile(0.90),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "max": ordered[-1],
    }


def _group_status_counts(
    records: list[dict[str, Any]],
    field: str,
    statuses: Sequence[str],
) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = {}
    for record in records:
        group = str(record.get("parent_group") or "")
        grouped.setdefault(group, Counter())[str(record.get(field))] += 1
    return {
        group: {
            "total_files": sum(counter.values()),
            **{status: counter.get(status, 0) for status in statuses},
        }
        for group, counter in sorted(grouped.items())
    }


def _error_counts_by_parent_group(
    error_rows: list[dict[str, str]],
    records_by_id: dict[str, dict[str, Any]],
) -> dict[str, int]:
    grouped: Counter[str] = Counter()
    for error in error_rows:
        record = records_by_id.get(error.get("file_instance_id", ""), {})
        grouped[str(record.get("parent_group") or "<unknown>")] += 1
    return dict(sorted(grouped.items()))


def _unmatched_filename_examples(
    records: list[dict[str, Any]],
    limit: int = FULL_MAX_UNMATCHED_FILENAME_EXAMPLES,
) -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    for record in records:
        if record.get("filename_parse_status") != "unmatched":
            continue
        examples.append(
            {
                "source_root_id": str(record["source_root_id"]),
                "parent_group": str(record.get("parent_group") or ""),
                "file_name": str(record["file_name"]),
                "relative_path": str(record["relative_path"]),
            }
        )
    return examples[:limit]


def _full_statistics(
    file_records: list[dict[str, Any]],
    error_rows: list[dict[str, str]],
    *,
    selected_count: int,
    source_snapshot_before: SourceSnapshot,
    source_snapshot_after: SourceSnapshot,
    source_snapshot_diff: dict[str, Any],
    runtime_snapshot: dict[str, Any],
    run_status: str,
    wall_time_seconds: float,
    checkpoint_write_time_seconds: float,
    resume_startup_time_seconds: float,
    resume_count: int,
    checkpoint_reused_count: int,
    checkpoint_reprocessed_count: int,
    retry_attempts_total: int,
    files_recovered_by_retry: int,
    retry_exhausted_count: int,
) -> dict[str, Any]:
    records_by_id = {record["file_instance_id"]: record for record in file_records}
    text_statuses = ("text_present", "text_absent", "mixed_or_uncertain", "check_failed")
    filename_statuses = ("matched", "unmatched", "error")
    text_counts = Counter(str(record.get("text_layer_status")) for record in file_records)
    filename_counts = Counter(str(record.get("filename_parse_status")) for record in file_records)
    error_stage_counts = Counter(str(error.get("stage")) for error in error_rows)
    error_category_counts = Counter(str(error.get("error_category")) for error in error_rows)
    duplicate_rows = group_exact_duplicates(file_records)
    duplicate_group_sizes = {
        str(row["duplicate_group_id"]): int(row["group_size"])
        for row in duplicate_rows
    }
    total_files = len(file_records)
    total_bytes = sum(int(record["size_bytes"] or 0) for record in file_records)
    wall_time = wall_time_seconds if wall_time_seconds else 0.0
    zero_page_count = sum(record.get("page_count") == 0 for record in file_records)
    filename_denominator = sum(filename_counts.get(status, 0) for status in filename_statuses)

    return {
        "run_status": run_status,
        "total_files": total_files,
        "selected_files": selected_count,
        "sampled_files": selected_count,
        "processed_files": total_files,
        "processed_unique_file_instances": len(records_by_id),
        "successful_files": sum(record.get("inventory_status") == "success" for record in file_records),
        "partial_files": sum(record.get("inventory_status") == "partial" for record in file_records),
        "failed_files": sum(record.get("inventory_status") == "failed" for record in file_records),
        "total_bytes": total_bytes,
        "file_size_distribution": _distribution(
            [int(record["size_bytes"]) for record in file_records if record.get("size_bytes") is not None]
        ),
        "page_count_distribution": _distribution(
            [int(record["page_count"]) for record in file_records if record.get("page_count") is not None]
        ),
        "pdf_open_success_count": sum(record.get("pdf_open_status") == "success" for record in file_records),
        "pdf_open_failure_count": sum(record.get("pdf_open_status") == "failed" for record in file_records),
        "pdf_open_error_count": sum(record.get("pdf_open_status") == "failed" for record in file_records),
        "pdf_status_counts": dict(sorted(Counter(str(record.get("pdf_status")) for record in file_records).items())),
        "valid_count": sum(record.get("pdf_status") == "valid" for record in file_records),
        "encrypted_count": sum(record.get("pdf_status") == "encrypted" for record in file_records),
        "corrupted_or_invalid_count": sum(
            record.get("pdf_status") == "corrupted_or_invalid" for record in file_records
        ),
        "zero_page_count": zero_page_count,
        "zero_page_error_count": error_category_counts.get("zero_page_count", 0),
        "hash_failure_count": error_stage_counts.get("hash", 0),
        "text_sample_failure_count": error_stage_counts.get("text_sample", 0),
        "source_consistency_failure_count": (
            error_stage_counts.get("source_consistency", 0)
            + error_stage_counts.get("resume_consistency", 0)
        ),
        "text_present_count": text_counts.get("text_present", 0),
        "text_absent_count": text_counts.get("text_absent", 0),
        "mixed_or_uncertain_count": text_counts.get("mixed_or_uncertain", 0),
        "text_check_failed_count": text_counts.get("check_failed", 0),
        "text_layer_by_parent_group": _group_status_counts(
            file_records, "text_layer_status", text_statuses
        ),
        "filename_matched_count": filename_counts.get("matched", 0),
        "filename_unmatched_count": filename_counts.get("unmatched", 0),
        "filename_error_count": filename_counts.get("error", 0),
        "filename_match_rate": (
            filename_counts.get("matched", 0) / filename_denominator
            if filename_denominator
            else 0.0
        ),
        "filename_by_parent_group": _group_status_counts(
            file_records, "filename_parse_status", filename_statuses
        ),
        "unmatched_filename_pattern_examples": _unmatched_filename_examples(file_records),
        "exact_duplicate_group_count": len(duplicate_group_sizes),
        "exact_duplicate_file_count": len(duplicate_rows),
        "duplicate_rate": len(duplicate_rows) / total_files if total_files else 0.0,
        "largest_duplicate_group_size": max(duplicate_group_sizes.values(), default=0),
        "error_count": len(error_rows),
        "error_stage_counts": dict(sorted(error_stage_counts.items())),
        "error_category_counts": dict(sorted(error_category_counts.items())),
        "error_parent_group_counts": _error_counts_by_parent_group(error_rows, records_by_id),
        "error_breakdown": {
            "stage": dict(sorted(error_stage_counts.items())),
            "category": dict(sorted(error_category_counts.items())),
            "parent_group": _error_counts_by_parent_group(error_rows, records_by_id),
        },
        "retry_attempts_total": retry_attempts_total,
        "files_recovered_by_retry": files_recovered_by_retry,
        "retry_exhausted_count": retry_exhausted_count,
        "source_changed_count": sum(
            bool(record.get("source_changed_during_run")) for record in file_records
        ),
        "source_consistency_issue_count": (
            sum(bool(record.get("source_changed_during_run")) for record in file_records)
            + sum(
                error.get("stage") in {"source_consistency", "resume_consistency"}
                for error in error_rows
            )
        ),
        "source_changed_since_checkpoint_count": error_category_counts.get(
            "source_changed_since_checkpoint", 0
        ),
        "checkpoint_batch_size": runtime_snapshot["checkpoint_batch_size"],
        "resume_count": resume_count,
        "checkpoint_reused_count": checkpoint_reused_count,
        "checkpoint_reprocessed_count": checkpoint_reprocessed_count,
        "checkpoint_write_time_seconds": checkpoint_write_time_seconds,
        "resume_startup_time_seconds": resume_startup_time_seconds,
        "wall_time_seconds": wall_time_seconds,
        "files_per_second": total_files / wall_time if wall_time else 0.0,
        "mib_per_second": total_bytes / (1024 * 1024) / wall_time if wall_time else 0.0,
        "runtime_snapshot": runtime_snapshot,
        "source_snapshot_before": source_snapshot_before.summary(),
        "source_snapshot_after": source_snapshot_after.summary(),
        "source_snapshot_fingerprint_before": source_snapshot_before.source_snapshot_fingerprint,
        "source_snapshot_fingerprint_after": source_snapshot_after.source_snapshot_fingerprint,
        "source_snapshot_match": bool(source_snapshot_diff["match"]),
        "source_snapshot_diff": source_snapshot_diff,
        "selected_count_matches_processed": total_files == selected_count,
    }


def _full_verdict(
    *,
    dirty: bool,
    processed_count: int,
    selected_count: int,
    source_snapshot_match: bool,
    source_consistency_issue_count: int,
    prior_integrity_match: bool,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if dirty:
        reasons.append("git working tree was dirty")
    if processed_count != selected_count:
        reasons.append("processed_count does not equal selected_count")
    if not source_snapshot_match:
        reasons.append("pre/post source snapshots differ")
    if source_consistency_issue_count:
        reasons.append("source consistency issues were recorded")
    if not prior_integrity_match:
        reasons.append("prior D1/D2/D3 Canonical Artifacts changed")
    return ("PASS" if not reasons else "HOLD"), reasons


def _validate_full_artifacts(
    run_directory: Path,
    *,
    selected_count: int,
    sample_manifest_hash: str,
) -> dict[str, Any]:
    """Validate Full canonical files, schemas, row accounting and checksums."""

    missing = [name for name in ARTIFACT_NAMES if not (run_directory / name).is_file()]
    if missing:
        raise PipelineError("Full canonical artifacts are missing: " + ", ".join(missing))

    files_table = pq.read_table(run_directory / "files.parquet")
    duplicate_table = pq.read_table(run_directory / "duplicate_groups.parquet")
    errors_table = pq.read_table(run_directory / "errors.parquet")
    if not files_table.schema.equals(files_schema()):
        raise PipelineError("Full files.parquet schema validation failed")
    if not duplicate_table.schema.equals(duplicate_groups_schema()):
        raise PipelineError("Full duplicate_groups.parquet schema validation failed")
    if not errors_table.schema.equals(errors_schema()):
        raise PipelineError("Full errors.parquet schema validation failed")
    if files_table.num_rows != selected_count:
        raise PipelineError(
            f"Full files.parquet row count mismatch: {files_table.num_rows} != {selected_count}"
        )

    sample_payload = _read_json_mapping(
        run_directory / "sample_manifest.json", "Full selection manifest"
    )
    if _sha256_bytes((run_directory / "sample_manifest.json").read_bytes()) != sample_manifest_hash:
        raise PipelineError("Full selection manifest checksum validation failed")
    items = sample_payload.get("items")
    if not isinstance(items, list) or len(items) != selected_count:
        raise PipelineError("Full selection manifest item count validation failed")
    if sample_payload.get("actual_count") != selected_count:
        raise PipelineError("Full selection manifest actual_count validation failed")

    file_records = files_table.to_pylist()
    file_ids = [record.get("file_instance_id") for record in file_records]
    sample_ids = [item.get("file_instance_id") for item in items if isinstance(item, dict)]
    if len(set(file_ids)) != selected_count or set(file_ids) != set(sample_ids):
        raise PipelineError("Full selected File Instance accounting validation failed")

    statistics = _read_json_mapping(run_directory / "statistics.json", "Full statistics")
    manifest = _read_json_mapping(run_directory / "manifest.json", "Full manifest")
    descriptors = manifest.get("output_artifacts")
    if not isinstance(descriptors, list) or len(descriptors) != len(ARTIFACT_NAMES):
        raise PipelineError("Full manifest output_artifacts validation failed")
    descriptor_by_name = {item.get("path"): item for item in descriptors if isinstance(item, dict)}
    if set(descriptor_by_name) != set(ARTIFACT_NAMES):
        raise PipelineError("Full manifest artifact path set validation failed")

    for artifact_name in ARTIFACT_NAMES:
        artifact_path = run_directory / artifact_name
        descriptor = descriptor_by_name[artifact_name]
        if descriptor.get("size_bytes") != artifact_path.stat().st_size:
            raise PipelineError(f"Full artifact size checksum validation failed: {artifact_name}")
        if artifact_name != "manifest.json":
            if descriptor.get("sha256") != sha256_path(artifact_path):
                raise PipelineError(f"Full artifact SHA-256 validation failed: {artifact_name}")

    normalized_manifest = dict(manifest)
    normalized_manifest["output_artifacts"] = [
        {
            **item,
            "sha256": "0" * 64,
        }
        if item.get("path") == "manifest.json"
        else item
        for item in descriptors
    ]
    manifest_descriptor = descriptor_by_name["manifest.json"]
    if manifest_descriptor.get("sha256") != _sha256_bytes(json_bytes(normalized_manifest)):
        raise PipelineError("Full normalized manifest SHA-256 validation failed")

    return {
        "status": "passed",
        "canonical_artifact_count": len(ARTIFACT_NAMES),
        "files_rows": files_table.num_rows,
        "duplicate_group_rows": duplicate_table.num_rows,
        "error_rows": errors_table.num_rows,
        "selection_manifest_items": len(items),
        "statistics_keys": len(statistics),
        "schema_validation": "passed",
        "checksum_validation": "passed",
        "row_accounting": "passed",
    }


def run_full(
    config: EnvironmentConfig,
    prior_run_ids: Sequence[str] | None = None,
    repo_root: str | Path = ".",
    run_id: str | None = None,
    *,
    resume: bool = False,
    expected_pdf_count: int | None = FULL_EXPECTED_PDF_COUNT,
    expected_top_level_group_count: int | None = FULL_EXPECTED_TOP_LEVEL_GROUP_COUNT,
    checkpoint_batch_size: int = FULL_CHECKPOINT_BATCH_SIZE,
) -> FullRunResult:
    """Run or resume the complete Full Inventory for all eligible PDFs."""

    if expected_pdf_count is not None and (
        isinstance(expected_pdf_count, bool) or expected_pdf_count < 1
    ):
        raise PipelineError("Full expected_pdf_count must be positive when provided")
    if expected_top_level_group_count is not None and (
        isinstance(expected_top_level_group_count, bool)
        or expected_top_level_group_count < 1
    ):
        raise PipelineError(
            "Full expected_top_level_group_count must be positive when provided"
        )
    if isinstance(checkpoint_batch_size, bool) or checkpoint_batch_size < 1:
        raise PipelineError("Full checkpoint_batch_size must be positive")
    if resume and not run_id:
        raise PipelineError("Full resume requires an existing run_id")
    if run_id is not None:
        _validate_simple_run_id(run_id, "full-")

    active_roots, output_root = _active_roots_and_safe_output(config)
    started_clock = time.perf_counter()
    repo_root = Path(repo_root).resolve()
    git_commit, dirty = _git_provenance(repo_root)
    if run_id is None:
        git_suffix = git_commit[:7] if git_commit != "unknown" else "unknown"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"full-{timestamp}-{git_suffix}"

    discovered = _discover_active_roots(active_roots)
    source_snapshot_current = capture_source_snapshot(discovered)
    prior_snapshot = _latest_full_source_snapshot(output_root, active_roots)
    _full_preflight_gate(
        source_snapshot_current,
        expected_pdf_count=expected_pdf_count,
        expected_top_level_group_count=expected_top_level_group_count,
        prior_snapshot=prior_snapshot,
    )

    sample_manifest = _full_sample_manifest(
        run_id,
        active_roots,
        discovered,
        expected_pdf_count if expected_pdf_count is not None else len(discovered),
    )
    sample_manifest_hash = _sha256_bytes(json_bytes(sample_manifest))
    config_fingerprint = _full_config_fingerprint(
        config,
        expected_pdf_count=expected_pdf_count,
        expected_top_level_group_count=expected_top_level_group_count,
        checkpoint_batch_size=checkpoint_batch_size,
    )
    selected_ids = {
        item["file_instance_id"] for item in sample_manifest["items"]
    }
    if len(selected_ids) != len(sample_manifest["items"]):
        raise PipelineError("Full selection contains duplicate File Instances")
    task_by_id = {
        task["file_instance_id"]: task
        for task in (
            _task_for(
                item,
                config.inventory.text_page_char_threshold,
                run_id,
                inventory_schema_version=FULL_INVENTORY_SCHEMA_VERSION,
                classify_zero_page_as_invalid=True,
            )
            for item in sorted(discovered, key=lambda value: (value.source_root_id, value.relative_path))
        )
    }
    tasks = [task_by_id[item_id] for item_id in (
        item["file_instance_id"] for item in sample_manifest["items"]
    )]
    if set(task_by_id) != selected_ids:
        raise PipelineError("Full selection/task File Instance accounting mismatch")

    prior_integrity_before = _full_prior_artifact_integrity(config, prior_run_ids)
    runtime_snapshot = _runtime_snapshot(output_root, config.inventory.worker_count, checkpoint_batch_size)
    run_directory = output_root / "inventory" / "runs" / run_id
    resume_startup_time_seconds = 0.0

    if resume:
        if not run_directory.is_dir():
            raise PipelineError(f"Full run directory does not exist: {run_directory}")
        state = _read_full_run_state(run_directory)
        if state.get("inventory_run_id") != run_id:
            raise PipelineError("Full run state inventory_run_id does not match run_id")
        if state.get("run_status") == "completed":
            raise PipelineError("a completed Full run is immutable and cannot be resumed")
        if state.get("run_status") not in FULL_RUN_STATES - {"completed"}:
            raise PipelineError(f"unsupported Full run state: {state.get('run_status')}")
        if state.get("inventory_schema_version") != FULL_INVENTORY_SCHEMA_VERSION:
            raise PipelineError("Full run state schema version does not match")
        if state.get("git_commit") != git_commit:
            raise PipelineError("Full resume requires the same Git commit")
        if state.get("config_fingerprint") != config_fingerprint:
            raise PipelineError("Full resume rejected: configuration fingerprint changed")
        if state.get("sample_manifest_hash") != sample_manifest_hash:
            raise PipelineError("Full resume rejected: selection manifest changed")
        if state.get("checkpoint_batch_size") != checkpoint_batch_size:
            raise PipelineError("Full resume requires the same checkpoint_batch_size")
        if state.get("target_count") != len(tasks):
            raise PipelineError("Full resume rejected: target count changed")
        sample_path = run_directory / "sample_manifest.json"
        if (
            not sample_path.is_file()
            or _sha256_bytes(sample_path.read_bytes()) != sample_manifest_hash
        ):
            raise PipelineError("Full resume rejected: persisted selection manifest changed")
        before_snapshot_path = run_directory / "source_snapshot_before.json"
        persisted_before = SourceSnapshot.from_dict(
            _read_json_mapping(before_snapshot_path, "Full source snapshot")
        )
        if (
            state.get("source_snapshot_before_fingerprint")
            != persisted_before.source_snapshot_fingerprint
        ):
            raise PipelineError("Full resume rejected: source snapshot fingerprint changed")
        if state.get("prior_artifact_integrity_before") != prior_integrity_before:
            raise PipelineError("Full resume rejected: prior Artifact integrity changed")
        unexpected_canonical = [
            name
            for name in ARTIFACT_NAMES
            if name != "sample_manifest.json" and (run_directory / name).exists()
        ]
        if unexpected_canonical:
            raise PipelineError(
                "Full active run contains canonical artifacts and cannot be safely resumed: "
                + ", ".join(unexpected_canonical)
            )
        checkpoint_records, checkpoint_errors = _load_full_checkpoints(
            run_directory,
            run_id,
            selected_ids,
        )
        source_snapshot_before = persisted_before
        resume_startup_time_seconds = time.perf_counter() - started_clock
        state["resume_count"] = int(state.get("resume_count", 0)) + 1
        state["run_status"] = "running"
        state["updated_at"] = _utc_now()
        state["resume_startup_time_seconds"] = resume_startup_time_seconds
        _write_full_run_state(run_directory, state)
    else:
        run_directory = create_run_directory(output_root, run_id)
        source_snapshot_before = source_snapshot_current
        write_json_atomic(
            sample_manifest,
            run_directory / "sample_manifest.json",
        )
        write_json_atomic(
            source_snapshot_before.as_dict(),
            run_directory / "source_snapshot_before.json",
        )
        state = {
            "inventory_run_id": run_id,
            "run_status": "running",
            "inventory_schema_version": FULL_INVENTORY_SCHEMA_VERSION,
            "git_commit": git_commit,
            "config_fingerprint": config_fingerprint,
            "sample_manifest_hash": sample_manifest_hash,
            "source_snapshot_before_fingerprint": source_snapshot_before.source_snapshot_fingerprint,
            "prior_artifact_integrity_before": prior_integrity_before,
            "started_at": _utc_now(),
            "updated_at": _utc_now(),
            "target_count": len(tasks),
            "requested_target_count": expected_pdf_count,
            "checkpoint_batch_size": checkpoint_batch_size,
            "completed_count": 0,
            "resume_count": 0,
            "checkpoint_reused_count": 0,
            "checkpoint_reprocessed_count": 0,
            "retry_attempts_total": 0,
            "files_recovered_by_retry": 0,
            "retry_exhausted_count": 0,
            "checkpoint_write_time_seconds": 0.0,
            "resume_startup_time_seconds": 0.0,
        }
        _write_full_run_state(run_directory, state)
        checkpoint_records = {}
        checkpoint_errors = []

    file_records: dict[str, dict[str, Any]] = {}
    error_rows: list[dict[str, str]] = []
    pending_tasks: list[dict[str, Any]] = []
    checkpoint_errors_by_id: dict[str, list[dict[str, str]]] = {}
    for error in checkpoint_errors:
        checkpoint_errors_by_id.setdefault(error["file_instance_id"], []).append(error)

    for task in tasks:
        item_id = task["file_instance_id"]
        checkpoint_record = checkpoint_records.get(item_id)
        if checkpoint_record is None:
            pending_tasks.append(task)
            continue
        try:
            current_stat = Path(task["path"]).stat()
        except OSError:
            current_stat = None
        if (
            current_stat is not None
            and checkpoint_record.get("size_bytes") == current_stat.st_size
            and checkpoint_record.get("mtime_ns") == current_stat.st_mtime_ns
        ):
            file_records[item_id] = checkpoint_record
            error_rows.extend(checkpoint_errors_by_id.get(item_id, []))
        else:
            pending_tasks.append(task)

    state["checkpoint_reused_count"] += len(file_records)
    reprocessed_from_checkpoint = len(checkpoint_records) - len(file_records)
    state["checkpoint_reprocessed_count"] += reprocessed_from_checkpoint
    if reprocessed_from_checkpoint:
        for item_id in checkpoint_records:
            if item_id in file_records:
                continue
            task = task_by_id[item_id]
            error_rows.append(
                _error_row(
                    task,
                    run_id,
                    {
                        "stage": "resume_consistency",
                        "error_category": "source_changed_since_checkpoint",
                        "error_message": (
                            "size or mtime differed from checkpoint; File Instance was reprocessed"
                        ),
                        "timestamp": _utc_now(),
                    },
                )
            )

    next_part_index = 0
    files_directory, _ = _checkpoint_paths(run_directory)
    if files_directory.exists():
        existing_parts = sorted(files_directory.glob("part-*.parquet"))
        if existing_parts:
            try:
                next_part_index = max(
                    int(path.stem.split("-")[-1]) for path in existing_parts
                ) + 1
            except (ValueError, IndexError) as exc:
                raise PipelineError("Full checkpoint part name is invalid") from exc

    try:
        for task_batch in _chunks(pending_tasks, checkpoint_batch_size):
            outcomes, retry_attempts, recovered, exhausted = _run_tasks_with_retries_detailed(
                task_batch,
                config.inventory.worker_count,
            )
            expected_batch_ids = {task["file_instance_id"] for task in task_batch}
            if set(outcomes) != expected_batch_ids:
                raise PipelineError("Full worker result set does not cover the entire batch")
            state["retry_attempts_total"] += retry_attempts
            state["files_recovered_by_retry"] += recovered
            state["retry_exhausted_count"] += exhausted
            batch_records = [outcomes[task["file_instance_id"]].record for task in task_batch]
            new_errors: list[dict[str, str]] = []
            for task in task_batch:
                outcome = outcomes[task["file_instance_id"]]
                new_errors.extend(
                    _error_row(task, run_id, error) for error in outcome.errors
                )
            batch_records.sort(
                key=lambda record: (record["source_root_id"], record["relative_path"])
            )
            new_errors.sort(
                key=lambda row: (
                    row["source_root_id"],
                    row["relative_path"],
                    row["stage"],
                    row["timestamp"],
                )
            )
            checkpoint_started = time.perf_counter()
            _write_full_checkpoint(run_directory, next_part_index, batch_records, new_errors)
            state["checkpoint_write_time_seconds"] += time.perf_counter() - checkpoint_started
            next_part_index += 1
            for record in batch_records:
                file_records[record["file_instance_id"]] = record
            error_rows.extend(new_errors)
            error_rows.sort(
                key=lambda row: (
                    row["source_root_id"],
                    row["relative_path"],
                    row["stage"],
                    row["timestamp"],
                )
            )
            state["completed_count"] = len(file_records)
            state["checkpoint_count"] = next_part_index
            state["updated_at"] = _utc_now()
            _write_full_run_state(run_directory, state)
    except KeyboardInterrupt:
        state["run_status"] = "interrupted"
        state["completed_count"] = len(file_records)
        state["updated_at"] = _utc_now()
        _write_full_run_state(run_directory, state)
        raise
    except Exception:
        state["run_status"] = "failed"
        state["completed_count"] = len(file_records)
        state["updated_at"] = _utc_now()
        _write_full_run_state(run_directory, state)
        raise

    file_records_list = sorted(
        file_records.values(),
        key=lambda record: (record["source_root_id"], record["relative_path"]),
    )
    if len(file_records_list) != len(tasks) or set(file_records) != selected_ids:
        state["run_status"] = "failed"
        state["completed_count"] = len(file_records_list)
        state["updated_at"] = _utc_now()
        _write_full_run_state(run_directory, state)
        raise PipelineError("Full processing did not account for every selected File Instance")

    try:
        post_discovered = _discover_active_roots(active_roots)
        source_snapshot_after = capture_source_snapshot(post_discovered)
        source_snapshot_diff = compare_source_snapshots(
            source_snapshot_before,
            source_snapshot_after,
        )
        write_json_atomic(
            source_snapshot_after.as_dict(),
            run_directory / "source_snapshot_after.json",
        )
        prior_integrity_after = _full_prior_artifact_integrity(config, prior_run_ids)
        prior_integrity_match = _prior_integrity_matches(
            prior_integrity_before,
            prior_integrity_after,
        )
        source_consistency_issue_count = sum(
            bool(record.get("source_changed_during_run"))
            for record in file_records_list
        ) + sum(
            error.get("stage") in {"source_consistency", "resume_consistency"}
            for error in error_rows
        )
        verdict, verdict_reasons = _full_verdict(
            dirty=dirty,
            processed_count=len(file_records_list),
            selected_count=len(tasks),
            source_snapshot_match=bool(source_snapshot_diff["match"]),
            source_consistency_issue_count=source_consistency_issue_count,
            prior_integrity_match=prior_integrity_match,
        )
        finished_at = _utc_now()
        wall_time_seconds = time.perf_counter() - started_clock
        duplicate_rows = group_exact_duplicates(file_records_list)
        statistics = _full_statistics(
            file_records_list,
            error_rows,
            selected_count=len(tasks),
            source_snapshot_before=source_snapshot_before,
            source_snapshot_after=source_snapshot_after,
            source_snapshot_diff=source_snapshot_diff,
            runtime_snapshot=runtime_snapshot,
            run_status="completed",
            wall_time_seconds=wall_time_seconds,
            checkpoint_write_time_seconds=state["checkpoint_write_time_seconds"],
            resume_startup_time_seconds=resume_startup_time_seconds,
            resume_count=state["resume_count"],
            checkpoint_reused_count=state["checkpoint_reused_count"],
            checkpoint_reprocessed_count=state["checkpoint_reprocessed_count"],
            retry_attempts_total=state["retry_attempts_total"],
            files_recovered_by_retry=state["files_recovered_by_retry"],
            retry_exhausted_count=state["retry_exhausted_count"],
        )
        statistics.update(
            {
                "full_inventory_verdict": verdict,
                "full_inventory_verdict_reasons": verdict_reasons,
                "prior_artifact_integrity_before": prior_integrity_before,
                "prior_artifact_integrity_after": prior_integrity_after,
                "prior_artifact_integrity_unchanged": prior_integrity_match,
            }
        )
        manifest: dict[str, Any] = {
            "inventory_run_id": run_id,
            "inventory_schema_version": FULL_INVENTORY_SCHEMA_VERSION,
            "run_status": "completed",
            "hostname": socket.gethostname(),
            "git_commit": git_commit,
            "dirty": dirty,
            "python_version": platform.python_version(),
            "tool_versions": _tool_versions(),
            "runtime_snapshot": runtime_snapshot,
            "source_roots": [root.snapshot() for root in active_roots],
            "migb_data_root": str(config.migb_data_root),
            "config_snapshot": config.snapshot(),
            "config_fingerprint": config_fingerprint,
            "selection_stage": "full",
            "selection_method": FULL_SELECTION_METHOD,
            "sampling_stage": "full",
            "sampling_method": FULL_SELECTION_METHOD,
            "sample_manifest_hash": sample_manifest_hash,
            "source_snapshot_before": source_snapshot_before.summary(),
            "source_snapshot_after": source_snapshot_after.summary(),
            "source_snapshot_fingerprint_before": source_snapshot_before.source_snapshot_fingerprint,
            "source_snapshot_fingerprint_after": source_snapshot_after.source_snapshot_fingerprint,
            "source_snapshot_match": bool(source_snapshot_diff["match"]),
            "source_snapshot_diff": source_snapshot_diff,
            "expected_pdf_count": expected_pdf_count,
            "expected_top_level_group_count": expected_top_level_group_count,
            "discovered_count": source_snapshot_before.discovered_count,
            "selected_count": len(tasks),
            "sampled_count": len(tasks),
            "processed_count": len(file_records_list),
            "success_count": statistics["successful_files"],
            "partial_count": statistics["partial_files"],
            "failure_count": statistics["failed_files"],
            "total_bytes": statistics["total_bytes"],
            "worker_count": config.inventory.worker_count,
            "checkpoint_batch_size": checkpoint_batch_size,
            "resume_count": state["resume_count"],
            "checkpoint_reused_count": state["checkpoint_reused_count"],
            "checkpoint_reprocessed_count": state["checkpoint_reprocessed_count"],
            "retry_attempts_total": state["retry_attempts_total"],
            "files_recovered_by_retry": state["files_recovered_by_retry"],
            "retry_exhausted_count": state["retry_exhausted_count"],
            "source_safety_check": "passed",
            "started_at": state["started_at"],
            "completed_at": finished_at,
            "full_inventory_verdict": verdict,
            "full_inventory_verdict_reasons": verdict_reasons,
            "prior_run_ids": list(prior_run_ids or ()),
            "prior_artifact_integrity_before": prior_integrity_before,
            "prior_artifact_integrity_after": prior_integrity_after,
            "prior_artifact_integrity_unchanged": prior_integrity_match,
            "output_artifacts": [],
        }

        write_parquet_atomic(file_records_list, run_directory / "files.parquet", files_schema())
        write_parquet_atomic(
            duplicate_rows,
            run_directory / "duplicate_groups.parquet",
            duplicate_groups_schema(),
        )
        write_parquet_atomic(error_rows, run_directory / "errors.parquet", errors_schema())
        write_json_atomic(statistics, run_directory / "statistics.json")
        manifest["artifact_validation"] = {
            "status": "passed",
            "canonical_artifact_count": len(ARTIFACT_NAMES),
            "schema_validation": "passed",
            "row_accounting": "passed",
            "checksum_validation": "passed",
        }
        _write_d3_manifest_with_checksums(run_directory, manifest)
        artifact_validation = _validate_full_artifacts(
            run_directory,
            selected_count=len(tasks),
            sample_manifest_hash=sample_manifest_hash,
        )
        state["run_status"] = "completed"
        state["completed_count"] = len(file_records_list)
        state["updated_at"] = _utc_now()
        state["checkpoint_count"] = next_part_index
        state["full_inventory_verdict"] = verdict
        _write_full_run_state(run_directory, state)
        return FullRunResult(
            run_id=run_id,
            run_directory=run_directory,
            manifest=manifest,
            statistics=statistics,
            run_status="completed",
            artifact_validation=artifact_validation,
        )
    except KeyboardInterrupt:
        state["run_status"] = "interrupted"
        state["completed_count"] = len(file_records_list)
        state["updated_at"] = _utc_now()
        _write_full_run_state(run_directory, state)
        raise
    except Exception:
        state["run_status"] = "failed"
        state["completed_count"] = len(file_records_list)
        state["updated_at"] = _utc_now()
        _write_full_run_state(run_directory, state)
        raise
