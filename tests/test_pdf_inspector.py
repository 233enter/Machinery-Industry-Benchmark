from __future__ import annotations

from pathlib import Path

import pytest

from migb.inventory.pdf_inspector import (
    classify_text_layer,
    inspect_pdf,
    sampled_page_indices,
)


@pytest.mark.parametrize(
    ("counts", "failures", "expected"),
    [
        ([50, 80], 0, "text_present"),
        ([0, 0], 0, "text_absent"),
        ([0, 80], 0, "mixed_or_uncertain"),
        ([], 2, "check_failed"),
    ],
)
def test_text_layer_classification_statuses(
    counts: list[int], failures: int, expected: str
) -> None:
    assert classify_text_layer(counts, failures, 50) == expected


@pytest.mark.parametrize(
    ("page_count", "expected"),
    [
        (0, ()),
        (1, (0,)),
        (2, (0, 1)),
        (3, (0, 1, 2)),
        (4, (0, 2, 3)),
    ],
)
def test_sampled_page_indices_deduplicates_short_documents(
    page_count: int, expected: tuple[int, ...]
) -> None:
    assert sampled_page_indices(page_count) == expected


def test_inspect_pdf_text_present_three_pages(
    tmp_path: Path, make_pdf, long_text: str
) -> None:
    path = make_pdf(tmp_path / "present.pdf", [long_text, long_text, long_text])

    result = inspect_pdf(path, text_page_char_threshold=50)

    assert result["pdf_open_status"] == "success"
    assert result["pdf_status"] == "valid"
    assert result["page_count"] == 3
    assert result["sampled_page_count"] == 3
    assert result["text_layer_status"] == "text_present"
    assert result["errors"] == []


def test_inspect_pdf_text_absent_one_page(tmp_path: Path, make_pdf) -> None:
    path = make_pdf(tmp_path / "absent.pdf", [None])

    result = inspect_pdf(path, text_page_char_threshold=50)

    assert result["page_count"] == 1
    assert result["sampled_page_count"] == 1
    assert result["sampled_text_char_count"] == 0
    assert result["text_layer_status"] == "text_absent"


def test_inspect_pdf_text_mixed_two_pages(
    tmp_path: Path, make_pdf, long_text: str
) -> None:
    path = make_pdf(tmp_path / "mixed.pdf", [long_text, None])

    result = inspect_pdf(path, text_page_char_threshold=50)

    assert result["page_count"] == 2
    assert result["sampled_page_count"] == 2
    assert result["text_layer_status"] == "mixed_or_uncertain"


def test_inspect_pdf_open_failure_is_check_failed(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a valid PDF")

    result = inspect_pdf(path, text_page_char_threshold=50)

    assert result["pdf_open_status"] == "failed"
    assert result["pdf_status"] == "unknown"
    assert result["text_layer_status"] == "check_failed"
    assert result["errors"]
