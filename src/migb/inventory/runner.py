"""D1 runner with process-isolated PyMuPDF work."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import socket
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import ARTIFACT_NAMES, create_run_directory, group_exact_duplicates, write_d1_artifacts
from .config import EnvironmentConfig
from .discovery import DiscoveredFile, DiscoveryError, discover_pdfs
from .filename_parser import parse_filename
from .hashing import sha256_file
from .identity import file_instance_id
from .pdf_inspector import inspect_pdf
from .safety import SafetyError, assert_output_path_safe
from .sampling import D1Sample, D2Sample, select_d1, select_d2
from .schema import INVENTORY_SCHEMA_VERSION


class PipelineError(RuntimeError):
    """Raised when a D1 run cannot be started or completed safely."""


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
        raise PipelineError("D1/D2 requires inventory.worker_count = 4")
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
