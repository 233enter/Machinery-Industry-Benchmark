"""D1 Artifact writers and duplicate grouping."""

from __future__ import annotations

import json
from pathlib import Path
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
