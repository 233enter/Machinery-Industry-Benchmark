from __future__ import annotations

import pytest

from migb.phase2.ocr import (
    OCRDetection,
    OCRPageResult,
    assemble_evidence,
    normalize_detections,
    select_page_indices,
)


def test_select_page_indices_matches_evidence_v02_contract() -> None:
    assert select_page_indices(10) == [0, 1, 2, 4, 6]
    assert select_page_indices(5) == [0, 1, 2, 3]
    assert select_page_indices(3) == [0, 1, 2]
    assert select_page_indices(1) == [0]


def test_normalize_detections_sorts_by_bbox_reading_order() -> None:
    detections = normalize_detections(
        (
            [
                [[100, 40], [120, 40], [120, 60], [100, 60]],
                [[10, 10], [30, 10], [30, 30], [10, 30]],
            ],
            ["second", "first"],
            [0.9, 0.8],
        )
    )
    assert [item.text for item in detections] == ["first", "second"]
    assert [item.score for item in detections] == [0.8, 0.9]


def test_assemble_evidence_applies_page_and_global_caps() -> None:
    page_results = [
        OCRPageResult(
            page_index=0,
            render_dpi=200,
            detections=(OCRDetection("a" * 6, 0.9, ()),),
            ocr_runtime_seconds=0.1,
        ),
        OCRPageResult(
            page_index=2,
            render_dpi=200,
            detections=(OCRDetection("b" * 6, 0.9, ()),),
            ocr_runtime_seconds=0.2,
        ),
    ]

    result = assemble_evidence(
        page_results,
        per_page_char_cap=4,
        global_char_cap=100,
    )

    assert result["evidence_page_indices"] == [0, 2]
    assert result["ocr_raw_char_count"] == 12
    assert result["page_metrics"] == [
        {
            "page_index": 0,
            "raw_char_count": 6,
            "stored_char_count": 4,
            "page_truncated": True,
        },
        {
            "page_index": 2,
            "raw_char_count": 6,
            "stored_char_count": 4,
            "page_truncated": True,
        },
    ]
    assert result["evidence_truncated"] is False
    assert result["ocr_runtime_seconds"] == pytest.approx(0.3)
    assert "<<<PAGE:0>>>" in result["evidence_text"]
    assert "<<<PAGE:2>>>" in result["evidence_text"]
