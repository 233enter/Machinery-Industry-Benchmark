"""D1 runner with process-isolated PyMuPDF work."""

from __future__ import annotations

import importlib.metadata
import hashlib
import json
import platform
import socket
import subprocess
import time
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
    write_d1_artifacts,
    write_json_atomic,
    write_parquet,
    write_parquet_atomic,
)
from .config import EnvironmentConfig
from .discovery import DiscoveredFile, DiscoveryError, discover_pdfs
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
    INVENTORY_SCHEMA_VERSION,
    duplicate_groups_schema,
    errors_schema,
    files_schema,
)


class PipelineError(RuntimeError):
    """Raised when a D1 run cannot be started or completed safely."""


D3_CHECKPOINT_BATCH_SIZE = 100
D3_MAX_RETRIES = 2
D3_RETRY_BACKOFF_SECONDS = (0.5, 2.0)
D3_RUN_STATES = frozenset({"running", "interrupted", "completed", "failed"})


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


def _task_for(item: DiscoveredFile, threshold: int, run_id: str) -> dict[str, Any]:
    return {
        "path": str(item.path),
        "source_root_id": item.source_root_id,
        "relative_path": item.relative_path,
        "file_name": item.file_name,
        "parent_group": item.parent_group,
        "extension": item.extension,
        "file_instance_id": file_instance_id(item.source_root_id, item.relative_path),
        "text_page_char_threshold": threshold,
        "inventory_run_id": run_id,
        "collected_at": _utc_now(),
    }


def _base_record(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
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

        inspection = inspect_pdf(path.as_posix(), task["text_page_char_threshold"])
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
        raise PipelineError("D1/D2/D3 requires inventory.worker_count = 4")
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


def _run_tasks_with_retries(
    tasks: list[dict[str, Any]],
    worker_count: int,
) -> tuple[dict[str, _TaskOutcome], int, int]:
    """Run a task batch with at most two bounded retries for transient I/O errors."""

    pending = {task["file_instance_id"]: task for task in tasks}
    final: dict[str, _TaskOutcome] = {}
    retry_attempts_total = 0
    recovered_by_retry = 0
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
                if attempt > 0 and not outcome.errors:
                    recovered_by_retry += 1
                final[item_id] = outcome
        if not retry_tasks:
            break
        retry_attempts_total += len(retry_tasks)
        time.sleep(D3_RETRY_BACKOFF_SECONDS[attempt])
        pending = retry_tasks
    return final, retry_attempts_total, recovered_by_retry


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
