from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from migb.inventory.artifacts import ARTIFACT_NAMES
from migb.inventory.config import EnvironmentConfig, InventorySettings, SourceRootConfig
from migb.inventory.runner import run_d1
from migb.inventory.schema import duplicate_groups_schema, errors_schema, files_schema


def test_run_d1_writes_six_artifacts_and_captures_pdf_failure(
    tmp_path: Path, make_pdf, long_text: str
) -> None:
    source_root = tmp_path / "source"
    output_root = tmp_path / "derived"

    for group_index in range(20):
        group = source_root / f"group-{group_index:02d}"
        if group_index == 0:
            make_pdf(group / "z-last.pdf", [long_text + " z"])
            make_pdf(group / "a-first.pdf", [long_text + " a"])
        elif group_index == 19:
            group.mkdir(parents=True, exist_ok=True)
            (group / "broken.pdf").write_bytes(b"not a valid PDF")
        else:
            make_pdf(group / f"【2025-{group_index:02d}】sample.pdf", [
                long_text + f" group {group_index}"
            ])

    source_files_before = sorted(
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*")
        if path.is_file()
    )
    config = EnvironmentConfig(
        source_roots=(SourceRootConfig("cmes_journal", source_root),),
        migb_data_root=output_root,
        inventory=InventorySettings(worker_count=4, text_page_char_threshold=50),
    )

    result = run_d1(config, repo_root=Path(__file__).parents[1], run_id="d1-local-test")

    run_directory = result.run_directory
    assert sorted(path.name for path in run_directory.iterdir()) == sorted(ARTIFACT_NAMES)
    assert result.manifest["sampled_count"] == 20
    assert result.manifest["processed_count"] == 20
    assert result.manifest["discovered_count"] == 21
    assert result.manifest["source_safety_check"] == "passed"
    assert result.manifest["worker_count"] == 4
    assert result.manifest["output_artifacts"] == list(ARTIFACT_NAMES)
    assert isinstance(result.manifest["dirty"], bool)
    assert result.manifest["git_commit"]

    sample_manifest = json.loads((run_directory / "sample_manifest.json").read_text())
    assert sample_manifest["sample_count"] == 20
    assert sample_manifest["sampling_method"] == (
        "first_by_sorted_relative_path_per_parent_group"
    )
    assert sample_manifest["items"][0]["relative_path"] == "group-00/a-first.pdf"
    assert {item["parent_group"] for item in sample_manifest["items"]} == {
        f"group-{index:02d}" for index in range(20)
    }

    files_table = pq.read_table(run_directory / "files.parquet")
    errors_table = pq.read_table(run_directory / "errors.parquet")
    duplicate_table = pq.read_table(run_directory / "duplicate_groups.parquet")
    assert files_table.num_rows == 20
    assert files_table.schema.equals(files_schema())
    assert errors_table.num_rows >= 1
    assert errors_table.schema.equals(errors_schema())
    assert duplicate_table.num_rows == 0
    assert duplicate_table.schema.equals(duplicate_groups_schema())

    statistics = json.loads((run_directory / "statistics.json").read_text())
    assert statistics["sampled_files"] == 20
    assert statistics["processed_files"] == 20
    assert statistics["partial_files"] == 1
    assert statistics["failed_files"] == 0
    assert statistics["pdf_open_error_count"] == 1
    assert statistics["error_count"] >= 1

    source_files_after = sorted(
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*")
        if path.is_file()
    )
    assert source_files_after == source_files_before
