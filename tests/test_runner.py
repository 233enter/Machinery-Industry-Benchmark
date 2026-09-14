from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

from migb.inventory.artifacts import ARTIFACT_NAMES
from migb.inventory.config import EnvironmentConfig, InventorySettings, SourceRootConfig
import pytest

from migb.inventory.runner import PipelineError, run_d1, run_d2, run_d3, run_full
from migb.inventory.schema import (
    FULL_INVENTORY_SCHEMA_VERSION,
    duplicate_groups_schema,
    errors_schema,
    files_schema,
)


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


def test_run_d2_excludes_d1_sample_and_records_sampling_metadata(
    tmp_path: Path, make_pdf, long_text: str
) -> None:
    source_root = tmp_path / "source"
    output_root = tmp_path / "derived"
    for group_index in range(2):
        group = source_root / f"group-{group_index:02d}"
        for file_index in range(11):
            make_pdf(
                group / f"item-{file_index:02d}.pdf",
                [long_text + f" group {group_index} item {file_index}"],
            )

    config = EnvironmentConfig(
        source_roots=(SourceRootConfig("cmes_journal", source_root),),
        migb_data_root=output_root,
        inventory=InventorySettings(worker_count=4, text_page_char_threshold=50),
    )
    d1_result = run_d1(
        config,
        repo_root=Path(__file__).parents[1],
        run_id="d1-local-isolation",
    )
    d1_manifest_before = (d1_result.run_directory / "sample_manifest.json").read_bytes()

    d2_result = run_d2(
        config,
        prior_run_id=d1_result.run_id,
        repo_root=Path(__file__).parents[1],
        run_id="d2-local-isolation",
    )

    d1_sample_ids = {
        item["file_instance_id"]
        for item in json.loads(d1_manifest_before.decode("utf-8"))["items"]
    }
    d2_sample = json.loads((d2_result.run_directory / "sample_manifest.json").read_text())
    assert d2_sample["sampling_stage"] == "d2"
    assert d2_sample["sampling_method"] == (
        "evenly_spaced_sorted_relative_path_per_parent_group_excluding_d1"
    )
    assert d2_sample["excluded_prior_run_id"] == "d1-local-isolation"
    assert d2_sample["excluded_prior_sample_count"] == 2
    assert d2_sample["excluded_prior_sample_found_count"] == 2
    assert d2_sample["excluded_prior_sample_missing_count"] == 0
    assert d2_sample["target_sample_count"] == 20
    assert d2_sample["actual_sample_count"] == 20
    assert len(d2_sample["items"]) == 20
    assert not d1_sample_ids & {
        item["file_instance_id"] for item in d2_sample["items"]
    }
    assert [item["actual_count"] for item in d2_sample["per_group_sample_count"]] == [10, 10]
    assert d2_result.manifest["processed_count"] == 20
    assert d2_result.manifest["actual_sample_count"] == 20
    assert d2_result.statistics["successful_files"] == 20
    assert d2_result.statistics["error_count"] == 0
    assert (d1_result.run_directory / "sample_manifest.json").read_bytes() == d1_manifest_before


def test_run_d3_controlled_stop_resume_and_finalization(
    tmp_path: Path, make_pdf, long_text: str
) -> None:
    source_root = tmp_path / "source"
    output_root = tmp_path / "derived"
    for group_index in range(2):
        group = source_root / f"group-{group_index:02d}"
        for file_index in range(14):
            make_pdf(
                group / f"item-{file_index:02d}.pdf",
                [long_text + f" group {group_index} item {file_index}"],
            )

    config = EnvironmentConfig(
        source_roots=(SourceRootConfig("cmes_journal", source_root),),
        migb_data_root=output_root,
        inventory=InventorySettings(worker_count=4, text_page_char_threshold=50),
    )
    repo_root = Path(__file__).parents[1]
    d1_result = run_d1(config, repo_root=repo_root, run_id="d1-local-d3-resume")
    d2_result = run_d2(
        config,
        prior_run_id=d1_result.run_id,
        repo_root=repo_root,
        run_id="d2-local-d3-resume",
    )

    interrupted = run_d3(
        config,
        prior_run_ids=(d1_result.run_id, d2_result.run_id),
        repo_root=repo_root,
        run_id="d3-local-resume",
        target_sample_count=10,
        checkpoint_batch_size=2,
        stop_after=2,
    )
    assert interrupted.run_status == "interrupted"
    assert interrupted.statistics["processed_files"] == 2
    state = json.loads((interrupted.run_directory / ".run_state.json").read_text())
    assert state["run_status"] == "interrupted"
    assert state["completed_count"] == 2
    assert len(list((interrupted.run_directory / "checkpoints" / "files").glob("*.parquet"))) == 1

    completed = run_d3(
        config,
        prior_run_ids=(d1_result.run_id, d2_result.run_id),
        repo_root=repo_root,
        run_id=interrupted.run_id,
        resume=True,
        target_sample_count=10,
        checkpoint_batch_size=2,
    )
    assert completed.run_status == "completed"
    assert completed.statistics["processed_files"] == 6
    assert completed.statistics["checkpoint_reused_count"] == 2
    assert completed.statistics["checkpoint_reprocessed_count"] == 0
    assert completed.manifest["run_status"] == "completed"
    assert completed.manifest["excluded_prior_item_count"] == 22
    assert completed.manifest["worker_count"] == 4
    assert all(isinstance(item, dict) for item in completed.manifest["output_artifacts"])
    assert sorted(path.name for path in completed.run_directory.iterdir() if path.name in ARTIFACT_NAMES) == sorted(ARTIFACT_NAMES)
    descriptors = {
        item["path"]: item for item in completed.manifest["output_artifacts"]
    }
    for artifact_name in ARTIFACT_NAMES:
        artifact_path = completed.run_directory / artifact_name
        assert descriptors[artifact_name]["size_bytes"] == artifact_path.stat().st_size
        if artifact_name != "manifest.json":
            assert descriptors[artifact_name]["sha256"] == hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest()
    normalized_manifest = json.loads(
        (completed.run_directory / "manifest.json").read_text()
    )
    normalized_manifest["output_artifacts"] = [
        {
            **item,
            "sha256": "0" * 64,
        }
        if item["path"] == "manifest.json"
        else item
        for item in normalized_manifest["output_artifacts"]
    ]
    assert descriptors["manifest.json"]["sha256"] == hashlib.sha256(
        (
            json.dumps(normalized_manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
    ).hexdigest()

    final_state = json.loads((completed.run_directory / ".run_state.json").read_text())
    assert final_state["run_status"] == "completed"
    assert final_state["completed_count"] == 6
    with pytest.raises(PipelineError, match="immutable"):
        run_d3(
            config,
            prior_run_ids=(d1_result.run_id, d2_result.run_id),
            repo_root=repo_root,
            run_id=completed.run_id,
            resume=True,
            target_sample_count=10,
            checkpoint_batch_size=2,
        )


def test_run_full_covers_all_files_and_uses_full_zero_page_semantics(
    tmp_path: Path, make_pdf, make_zero_page_pdf, long_text: str
) -> None:
    source_root = tmp_path / "source"
    output_root = tmp_path / "derived"
    make_pdf(source_root / "group-a" / "【2026-01】normal.pdf", [long_text])
    make_zero_page_pdf(source_root / "group-a" / "zero\npage.pdf")
    make_pdf(source_root / "group-b" / "text-absent.pdf", [None])

    config = EnvironmentConfig(
        source_roots=(SourceRootConfig("cmes_journal", source_root),),
        migb_data_root=output_root,
        inventory=InventorySettings(worker_count=4, text_page_char_threshold=50),
    )
    result = run_full(
        config,
        repo_root=Path(__file__).parents[1],
        run_id="full-local-test",
        expected_pdf_count=3,
        expected_top_level_group_count=2,
    )

    assert result.run_status == "completed"
    assert result.manifest["inventory_schema_version"] == FULL_INVENTORY_SCHEMA_VERSION
    assert result.manifest["selection_stage"] == "full"
    assert result.manifest["selection_method"] == (
        "all_eligible_pdf_in_configured_source_root"
    )
    assert result.manifest["selected_count"] == 3
    assert result.manifest["processed_count"] == 3
    assert result.manifest["checkpoint_batch_size"] == 500
    assert result.manifest["source_snapshot_match"] is True
    assert result.manifest["artifact_validation"]["checksum_validation"] == "passed"
    assert result.artifact_validation["status"] == "passed"

    sample_manifest = json.loads(
        (result.run_directory / "sample_manifest.json").read_text(encoding="utf-8")
    )
    assert sample_manifest["selection_stage"] == "full"
    assert sample_manifest["target_count"] == 3
    assert sample_manifest["actual_count"] == 3
    assert len(sample_manifest["items"]) == 3
    assert "group-a/zero\npage.pdf" in {
        item["relative_path"] for item in sample_manifest["items"]
    }

    files_table = pq.read_table(result.run_directory / "files.parquet")
    assert files_table.num_rows == 3
    assert files_table.schema.equals(files_schema())
    records = files_table.to_pylist()
    zero_page = next(record for record in records if record["page_count"] == 0)
    assert zero_page["inventory_schema_version"] == FULL_INVENTORY_SCHEMA_VERSION
    assert zero_page["pdf_status"] == "corrupted_or_invalid"
    assert zero_page["inventory_status"] == "partial"
    assert zero_page["text_layer_status"] == "check_failed"

    statistics = json.loads(
        (result.run_directory / "statistics.json").read_text(encoding="utf-8")
    )
    assert statistics["total_files"] == 3
    assert statistics["processed_files"] == 3
    assert statistics["corrupted_or_invalid_count"] == 1
    assert statistics["zero_page_count"] == 1
    assert statistics["text_check_failed_count"] == 1
    assert statistics["text_layer_by_parent_group"]["group-a"]["check_failed"] == 1
    assert statistics["filename_match_rate"] == pytest.approx(1 / 3)

    with pytest.raises(PipelineError, match="immutable"):
        run_full(
            config,
            repo_root=Path(__file__).parents[1],
            run_id=result.run_id,
            resume=True,
            expected_pdf_count=3,
            expected_top_level_group_count=2,
        )


def test_full_preflight_count_gate_reports_mismatch_without_creating_run(
    tmp_path: Path, make_pdf
) -> None:
    source_root = tmp_path / "source"
    output_root = tmp_path / "derived"
    make_pdf(source_root / "group" / "one.pdf", ["one"])
    config = EnvironmentConfig(
        source_roots=(SourceRootConfig("cmes_journal", source_root),),
        migb_data_root=output_root,
        inventory=InventorySettings(worker_count=4),
    )

    with pytest.raises(PipelineError, match="added_paths=.*missing_paths="):
        run_full(
            config,
            repo_root=Path(__file__).parents[1],
            run_id="full-preflight-mismatch",
            expected_pdf_count=2,
            expected_top_level_group_count=1,
        )
    assert not (output_root / "inventory" / "runs" / "full-preflight-mismatch").exists()
