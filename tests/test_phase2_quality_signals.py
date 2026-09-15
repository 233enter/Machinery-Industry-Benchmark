from __future__ import annotations

import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from migb.phase2.quality_signals import (
    OrRule,
    ThresholdRule,
    calculate_quality_signals,
    evaluate_trigger,
    is_cjk_char,
    is_private_use_char,
    is_unexpected_control_char,
    threshold_candidates,
)


def test_unicode_ranges_and_control_filtering_are_explicit() -> None:
    assert is_private_use_char("\uE000")
    assert is_private_use_char(chr(0xF0000))
    assert is_private_use_char(chr(0x100000))
    assert not is_private_use_char("A")

    assert is_unexpected_control_char("\x00")
    assert not is_unexpected_control_char("\t")
    assert not is_unexpected_control_char("\n")
    assert not is_unexpected_control_char("\r")

    assert is_cjk_char("机")
    assert is_cjk_char(chr(0x20000))
    assert is_cjk_char(chr(0x30000))
    assert not is_cjk_char("A")


def test_quality_signal_calculation_counts_required_categories() -> None:
    text = "A机1\t\n\r\x00\ufffd\uE000"
    signals = calculate_quality_signals(text)

    assert signals["total_chars"] == len(text)
    assert signals["replacement_char_count"] == 1
    assert signals["private_use_char_count"] == 1
    assert signals["control_char_count"] == 1
    assert signals["printable_char_count"] == 4
    assert signals["ascii_letter_count"] == 1
    assert signals["cjk_char_count"] == 1
    assert signals["digit_count"] == 1
    assert signals["whitespace_count"] == 3
    assert signals["suspicious_char_count"] == 3
    assert signals["suspicious_char_rate"] == pytest.approx(3 / len(text))
    assert signals["whitespace_ratio"] == pytest.approx(3 / len(text))


def test_empty_text_has_zero_rates_and_serializes() -> None:
    signals = calculate_quality_signals("")
    assert signals["total_chars"] == 0
    assert all(
        value == 0 or value == 0.0
        for name, value in signals.items()
        if name.endswith("_rate") or name.endswith("_ratio")
    )
    json.dumps(signals, ensure_ascii=False, sort_keys=True)


def test_quality_signals_round_trip_through_parquet(tmp_path) -> None:
    signals = calculate_quality_signals("机械 A-1")
    path = tmp_path / "quality_signals.parquet"
    pq.write_table(pa.Table.from_pylist([signals]), path)
    restored = pq.read_table(path).to_pylist()[0]
    assert restored["total_chars"] == signals["total_chars"]
    assert restored["cjk_char_count"] == signals["cjk_char_count"]
    assert restored["suspicious_char_rate"] == signals["suspicious_char_rate"]


def test_threshold_candidates_and_or_rule_are_deterministic() -> None:
    rows = [
        {"calibration_item_id": "a", "pool_name": "main", "control_char_rate": 0.0},
        {"calibration_item_id": "b", "pool_name": "main", "control_char_rate": 0.2},
        {"calibration_item_id": "c", "pool_name": "audit", "control_char_rate": None},
    ]
    assert threshold_candidates(rows, "control_char_rate", ">=") == (0.0, 0.2)
    with pytest.raises(ValueError, match="operator"):
        threshold_candidates(rows, "printable_char_ratio", ">=")
    left = ThresholdRule("control_char_rate", ">=", 0.2)
    right = ThresholdRule("printable_char_ratio", "<=", 0.9)
    rule = OrRule(left, right)
    assert rule.formula == (
        "control_char_rate >= 0.20000000000000001 OR printable_char_ratio <= 0.90000000000000002"
    )
    assert rule.matches({"control_char_rate": 0.2, "printable_char_ratio": 1.0})
    assert rule.matches({"control_char_rate": 0.0, "printable_char_ratio": 0.9})
    assert not rule.matches({"control_char_rate": 0.0, "printable_char_ratio": 1.0})


def test_trigger_evaluation_reports_recall_false_positives_and_main_rate() -> None:
    rows = [
        {
            "calibration_item_id": "positive",
            "pool_name": "main",
            "control_char_rate": 0.5,
        },
        {
            "calibration_item_id": "negative",
            "pool_name": "main",
            "control_char_rate": 0.5,
        },
        {
            "calibration_item_id": "other-main",
            "pool_name": "main",
            "control_char_rate": 0.0,
        },
    ]
    result = evaluate_trigger(
        rows,
        ThresholdRule("control_char_rate", ">=", 0.5),
        positive_ids={"positive"},
        negative_ids={"negative"},
    )
    assert result["garbled_recall"] == 1.0
    assert result["reviewed_false_positive_count"] == 1
    assert result["main_triggered_count"] == 2
    assert result["main_triggered_rate"] == pytest.approx(2 / 3)
