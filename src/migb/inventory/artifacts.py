"""D1 Artifact writers and duplicate grouping."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from .schema import duplicate_groups_schema, errors_schema, files_schema, write_parquet


ARTIFACT_NAMES = (
    "files.parquet",
    "duplicate_groups.parquet",
    "errors.parquet",
    "sample_manifest.json",
    "manifest.json",
    "statistics.json",
)


def create_run_directory(output_root: str | Path, run_id: str) -> Path:
    """Create one immutable run directory without overwriting an existing run."""

    run_parent = Path(output_root) / "inventory" / "runs"
    run_parent.mkdir(parents=True, exist_ok=True)
    run_directory = run_parent / run_id
    run_directory.mkdir()
    return run_directory


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize JSON with the same stable representation used by write_json."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _fsync_directory(directory: Path) -> None:
    """Persist a directory entry when the platform supports directory fsync."""

    try:
        directory_fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_write_bytes(data: bytes, path: str | Path) -> None:
    """Write bytes through a same-directory temp file and atomic rename."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            file_descriptor = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output)
        _fsync_directory(output.parent)
    finally:
        if file_descriptor != -1:
            os.close(file_descriptor)
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def write_json_atomic(payload: dict[str, Any], path: str | Path) -> None:
    """Write JSON with a durable temp-file-to-rename sequence."""

    _atomic_write_bytes(json_bytes(payload), path)


def write_parquet_atomic(
    rows: Iterable[dict[str, Any]],
    path: str | Path,
    schema,
) -> None:
    """Write a Parquet file atomically using an explicit schema."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    os.close(file_descriptor)
    file_descriptor = -1
    temporary_path = Path(temporary_name)
    try:
        write_parquet(rows, temporary_path, schema)
        with temporary_path.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary_path, output)
        _fsync_directory(output.parent)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def sha256_path(path: str | Path) -> str:
    """Return the streaming SHA-256 digest of one artifact."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_descriptor(path: str | Path, *, checksum_basis: str | None = None) -> dict[str, Any]:
    """Describe one materialized artifact for a manifest checksum record."""

    artifact_path = Path(path)
    descriptor: dict[str, Any] = {
        "path": artifact_path.name,
        "size_bytes": artifact_path.stat().st_size,
        "sha256": sha256_path(artifact_path),
    }
    if checksum_basis is not None:
        descriptor["checksum_basis"] = checksum_basis
    return descriptor


def group_exact_duplicates(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one row per member for exact duplicate groups only."""

    by_hash: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("hash_status") != "success" or not record.get("sha256"):
            continue
        by_hash.setdefault(str(record["sha256"]), []).append(record)

    rows: list[dict[str, Any]] = []
    for sha256 in sorted(by_hash):
        members = sorted(
            by_hash[sha256],
            key=lambda record: (
                record.get("source_root_id", ""),
                record.get("relative_path", ""),
            ),
        )
        if len(members) < 2:
            continue
        group_id = f"exact-{sha256}"
        for index, member in enumerate(members):
            rows.append(
                {
                    "duplicate_group_id": group_id,
                    "sha256": sha256,
                    "group_size": len(members),
                    "file_instance_id": member["file_instance_id"],
                    "is_representative": index == 0,
                }
            )
    return rows


def write_d1_artifacts(
    run_directory: str | Path,
    file_records: list[dict[str, Any]],
    duplicate_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
    sample_manifest: dict[str, Any],
    manifest: dict[str, Any],
    statistics: dict[str, Any],
) -> None:
    """Write every D1 Artifact, including valid zero-row Parquet files."""

    run_directory = Path(run_directory)
    write_parquet(file_records, run_directory / "files.parquet", files_schema())
    write_parquet(
        duplicate_rows,
        run_directory / "duplicate_groups.parquet",
        duplicate_groups_schema(),
    )
    write_parquet(error_rows, run_directory / "errors.parquet", errors_schema())
    write_json(sample_manifest, run_directory / "sample_manifest.json")
    write_json(manifest, run_directory / "manifest.json")
    write_json(statistics, run_directory / "statistics.json")
