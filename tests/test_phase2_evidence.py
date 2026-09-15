from __future__ import annotations

from pathlib import Path

from migb.inventory.identity import file_instance_id
from migb.phase2.evidence import (
    EVIDENCE_REVISION,
    assemble_evidence,
    extract_evidence,
    extract_evidence_task,
    normalize_page_text,
)


def _task(path: Path, page_count: int, *, item_suffix: str, not_applicable: bool = False) -> dict[str, object]:
    stat_result = path.stat()
    relative_path = f"group/{path.name}"
    return {
        "source_path": str(path),
        "phase2_run_id": "p2b-test",
        "calibration_sample_id": "sample-test",
        "calibration_item_id": f"item-{item_suffix}",
        "file_instance_id": file_instance_id("root", relative_path),
        "pool_name": "source_quality_exception" if not_applicable else "main",
        "relative_path": relative_path,
        "parent_group": "group",
        "sha256": "sha",
        "page_count": page_count,
        "text_layer_status": "text_present",
        "filename_title": "filename title",
        "metadata_title": "metadata title",
        "expected_size_bytes": stat_result.st_size,
        "expected_mtime_ns": stat_result.st_mtime_ns,
        "page_indices": [0, 1, 2],
        "max_extracted_chars": 12000,
        "evidence_revision": EVIDENCE_REVISION,
        "not_applicable": not_applicable,
    }


def test_one_two_and_four_page_documents_use_only_existing_first_pages(
    tmp_path: Path, make_pdf
) -> None:
    one = make_pdf(tmp_path / "one.pdf", ["page-0"])
    two = make_pdf(tmp_path / "two.pdf", ["page-0", "page-1"])
    four = make_pdf(tmp_path / "four.pdf", ["page-0", "page-1", "page-2", "page-3"])

    rows = extract_evidence(
        [
            _task(one, 1, item_suffix="one"),
            _task(two, 2, item_suffix="two"),
            _task(four, 4, item_suffix="four"),
        ],
        worker_count=2,
    )

    assert rows[0]["evidence_status"] == "success"
    assert rows[0]["evidence_page_indices"] == [0]
    assert rows[1]["evidence_page_indices"] == [0, 1]
    assert rows[2]["evidence_page_indices"] == [0, 1, 2]
    assert "page-3" not in rows[2]["evidence_text"]
    assert "<<<PAGE:0>>>" in rows[2]["evidence_text"]
    assert "<<<PAGE:2>>>" in rows[2]["evidence_text"]


def test_evidence_text_normalization_and_exact_character_cap() -> None:
    assert normalize_page_text("a\r\nb\rc") == "a\nb\nc"
    text, char_count, truncated, raw_count = assemble_evidence(
        [(0, "x" * 13000)],
        12000,
    )
    assert char_count == 12000
    assert len(text) == 12000
    assert truncated is True
    assert raw_count == 13000


def test_zero_text_extraction_is_success_not_failure(tmp_path: Path, make_pdf) -> None:
    path = make_pdf(tmp_path / "empty-pages.pdf", [None, None])
    row = extract_evidence_task(_task(path, 2, item_suffix="empty"))
    assert row["evidence_status"] == "success"
    assert row["raw_text_char_count"] == 0
    assert row["evidence_char_count"] > 0  # stable page delimiters remain
    assert row["source_changed_during_evidence"] is False


def test_source_quality_exception_is_not_applicable_without_opening_pdf(
    tmp_path: Path, make_zero_page_pdf
) -> None:
    path = make_zero_page_pdf(tmp_path / "zero.pdf")
    row = extract_evidence_task(
        _task(path, 0, item_suffix="zero", not_applicable=True)
    )
    assert row["evidence_status"] == "not_applicable"
    assert row["evidence_page_indices"] == []
    assert row["evidence_char_count"] == 0
    assert row["evidence_error_stage"] is None


def test_pre_extraction_source_mismatch_is_visible(tmp_path: Path, make_pdf) -> None:
    path = make_pdf(tmp_path / "changed.pdf", ["text"])
    task = _task(path, 1, item_suffix="changed")
    task["expected_size_bytes"] = int(task["expected_size_bytes"]) + 1
    row = extract_evidence_task(task)
    assert row["evidence_status"] == "failed"
    assert row["source_changed_during_evidence"] is True
    assert row["evidence_error_stage"] == "source_consistency"


def test_extract_evidence_restores_canonical_task_order(tmp_path: Path, make_pdf) -> None:
    first = make_pdf(tmp_path / "first.pdf", ["first"])
    second = make_pdf(tmp_path / "second.pdf", ["second"])
    tasks = [
        _task(first, 1, item_suffix="first"),
        _task(second, 1, item_suffix="second"),
    ]
    rows = extract_evidence(tasks, worker_count=2)
    assert [row["calibration_item_id"] for row in rows] == ["item-first", "item-second"]
