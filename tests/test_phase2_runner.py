from __future__ import annotations

import json
from pathlib import Path

import pytest

from migb.inventory.artifacts import (
    ARTIFACT_NAMES,
    write_json,
    write_parquet,
)
from migb.inventory.identity import file_instance_id
from migb.inventory.runner import _write_d3_manifest_with_checksums, process_file_task
from migb.inventory.schema import (
    FULL_INVENTORY_SCHEMA_VERSION,
    duplicate_groups_schema,
    errors_schema,
    files_schema,
)
from migb.phase2.config import (
    Phase2AuditConfig,
    Phase2Config,
    Phase2EvidenceConfig,
    Phase2InputConfig,
    Phase2SamplingConfig,
)
from migb.phase2.runner import run_phase2


def _make_full_inventory(
    tmp_path: Path,
    source_root: Path,
    output_root: Path,
    files: list[Path],
) -> Path:
    inventory_run_id = "full-test"
    run_directory = output_root / "inventory" / "runs" / inventory_run_id
    run_directory.mkdir(parents=True)
    records = []
    errors = []
    for path in files:
        relative_path = path.relative_to(source_root).as_posix()
        task = {
            "path": str(path),
            "source_root_id": "root",
            "relative_path": relative_path,
            "file_name": path.name,
            "parent_group": path.relative_to(source_root).parts[0],
            "extension": ".pdf",
            "file_instance_id": file_instance_id("root", relative_path),
            "text_page_char_threshold": 50,
            "inventory_schema_version": FULL_INVENTORY_SCHEMA_VERSION,
            "classify_zero_page_as_invalid": True,
            "inventory_run_id": inventory_run_id,
            "collected_at": "2026-01-01T00:00:00Z",
        }
        record, task_errors = process_file_task(task)
        records.append(record)
        errors.extend(
            {
                "inventory_run_id": inventory_run_id,
                "file_instance_id": record["file_instance_id"],
                "source_root_id": "root",
                "relative_path": relative_path,
                **error,
                "timestamp": "2026-01-01T00:00:00Z",
            }
            for error in task_errors
        )

    write_parquet(records, run_directory / "files.parquet", files_schema())
    write_parquet([], run_directory / "duplicate_groups.parquet", duplicate_groups_schema())
    write_parquet(errors, run_directory / "errors.parquet", errors_schema())
    write_json(
        {
            "inventory_run_id": inventory_run_id,
            "selection_stage": "full",
            "actual_count": len(records),
            "items": [
                {
                    "source_root_id": record["source_root_id"],
                    "parent_group": record["parent_group"],
                    "file_instance_id": record["file_instance_id"],
                    "relative_path": record["relative_path"],
                }
                for record in records
            ],
        },
        run_directory / "sample_manifest.json",
    )
    statistics = {
        "processed_files": len(records),
        "full_inventory_verdict": "PASS",
    }
    write_json(statistics, run_directory / "statistics.json")
    manifest = {
        "inventory_run_id": inventory_run_id,
        "inventory_schema_version": FULL_INVENTORY_SCHEMA_VERSION,
        "run_status": "completed",
        "hostname": "test-host",
        "git_commit": "full-test-commit",
        "dirty": False,
        "migb_data_root": str(output_root),
        "source_roots": [
            {
                "source_root_id": "root",
                "path": str(source_root),
                "access_policy": "read_only",
                "enabled": True,
            }
        ],
        "full_inventory_verdict": "PASS",
        "artifact_validation": {
            "status": "passed",
            "checksum_validation": "passed",
            "row_accounting": "passed",
            "schema_validation": "passed",
        },
    }
    _write_d3_manifest_with_checksums(run_directory, manifest)
    assert set(path.name for path in run_directory.iterdir()) == set(ARTIFACT_NAMES)
    return run_directory


def test_run_phase2_validates_full_inventory_and_writes_four_gate2b_artifacts(
    tmp_path: Path, make_pdf, make_zero_page_pdf, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "source"
    output_root = tmp_path / "output"
    files = [
        make_pdf(source_root / "group" / f"main-{index}.pdf", [f"main {index}"])
        for index in range(3)
    ]
    files.append(make_pdf(source_root / "other" / "text-absent.pdf", [None]))
    files.append(make_zero_page_pdf(source_root / "other" / "exception.pdf"))
    _make_full_inventory(tmp_path, source_root, output_root, files)
    monkeypatch.setattr("migb.phase2.runner.EXPECTED_FULL_FILE_COUNT", len(files))

    config = Phase2Config(
        input=Phase2InputConfig(
            inventory_run_id="full-test",
            inventory_root=output_root / "inventory" / "runs" / "full-test",
            source_root=source_root,
            migb_data_root=output_root,
        ),
        sampling=Phase2SamplingConfig(
            main_target=3,
            base_quota_per_parent_group=1,
            audit=Phase2AuditConfig(
                source_quality_exception="all",
                text_absent_target=1,
                mixed_text_target=1,
                filename_unmatched_target=1,
            ),
        ),
        evidence=Phase2EvidenceConfig(worker_count=2),
    )
    result = run_phase2(config, repo_root=tmp_path, run_id="p2b-local-test")

    assert result.gate2b_verdict == "PASS"
    assert result.statistics["main_actual"] == 3
    assert result.statistics["source_quality_exception_actual"] == 1
    assert result.statistics["text_absent_actual"] == 1
    assert result.statistics["total_unique_selected"] == 5
    assert result.statistics["main_audit_overlap_count"] == 0
    assert result.statistics["cross_pool_overlap_count"] == 0
    assert result.statistics["evidence_not_applicable_count"] == 1
    assert result.artifact_validation["checksum_validation"] == "passed"
    assert set(path.name for path in result.run_directory.iterdir()) == {
        "calibration_sample.parquet",
        "calibration_evidence.jsonl",
        "manifest.json",
        "statistics.json",
    }
    manifest = json.loads((result.run_directory / "manifest.json").read_text())
    assert manifest["stage"] == "gate2b"
    assert manifest["deterministic_recomputation_passed"] is True
