from __future__ import annotations

from migb.inventory.filename_parser import parse_filename


def test_filename_parser_matched() -> None:
    result = parse_filename("【2024-03】轴承\n强度分析.pdf")

    assert result.filename_parse_status == "matched"
    assert result.filename_year == "2024"
    assert result.filename_issue == "03"
    assert result.filename_title == "轴承\n强度分析"


def test_filename_parser_unmatched() -> None:
    result = parse_filename("no-structured-metadata.pdf")

    assert result.filename_parse_status == "unmatched"
    assert result.filename_year is None
    assert result.filename_title is None


def test_filename_parser_error() -> None:
    result = parse_filename(None)  # type: ignore[arg-type]

    assert result.filename_parse_status == "error"
    assert result.filename_year is None
