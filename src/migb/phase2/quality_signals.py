"""Deterministic Unicode quality signals for Evidence routing diagnostics."""

from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


QUALITY_SIGNAL_FIELDS = (
    "total_chars",
    "replacement_char_count",
    "replacement_char_rate",
    "private_use_char_count",
    "private_use_char_rate",
    "control_char_count",
    "control_char_rate",
    "printable_char_count",
    "printable_char_ratio",
    "ascii_letter_count",
    "cjk_char_count",
    "digit_count",
    "whitespace_count",
    "whitespace_ratio",
    "suspicious_char_count",
    "suspicious_char_rate",
)

ROUTING_SIGNAL_FIELDS = (
    "replacement_char_rate",
    "private_use_char_rate",
    "control_char_rate",
    "printable_char_ratio",
    "suspicious_char_rate",
)

_GE_SIGNALS = {
    "replacement_char_rate",
    "private_use_char_rate",
    "control_char_rate",
    "suspicious_char_rate",
}
_LE_SIGNALS = {"printable_char_ratio"}


def is_private_use_char(value: str) -> bool:
    """Return whether one Unicode code point is in a Unicode Private Use Area."""

    if len(value) != 1:
        raise ValueError("is_private_use_char expects exactly one character")
    codepoint = ord(value)
    return (
        0xE000 <= codepoint <= 0xF8FF
        or 0xF0000 <= codepoint <= 0xFFFFD
        or 0x100000 <= codepoint <= 0x10FFFD
    )


def is_unexpected_control_char(value: str) -> bool:
    """Return whether a character is a non-layout Unicode Cc control character."""

    if len(value) != 1:
        raise ValueError("is_unexpected_control_char expects exactly one character")
    return unicodedata.category(value) == "Cc" and value not in "\t\n\r"


def is_cjk_char(value: str) -> bool:
    """Return whether a character is a CJK ideograph in the supported ranges."""

    if len(value) != 1:
        raise ValueError("is_cjk_char expects exactly one character")
    codepoint = ord(value)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
        or 0x20000 <= codepoint <= 0x323AF
    )


def calculate_quality_signals(text: str) -> dict[str, int | float]:
    """Calculate deterministic, model-free signals over the stored Evidence text.

    ``total_chars`` is the Python Unicode code-point length of the stored Evidence
    string, including the established page delimiters. Rates use ``total_chars`` as
    their denominator and are zero for an empty string.
    """

    if not isinstance(text, str):
        raise TypeError("Evidence text must be a string")

    total_chars = len(text)
    replacement_char_count = 0
    private_use_char_count = 0
    control_char_count = 0
    printable_char_count = 0
    ascii_letter_count = 0
    cjk_char_count = 0
    digit_count = 0
    whitespace_count = 0

    for char in text:
        if char == "\ufffd":
            replacement_char_count += 1
        if is_private_use_char(char):
            private_use_char_count += 1
        if is_unexpected_control_char(char):
            control_char_count += 1
        if char.isprintable():
            printable_char_count += 1
        if ("A" <= char <= "Z") or ("a" <= char <= "z"):
            ascii_letter_count += 1
        if is_cjk_char(char):
            cjk_char_count += 1
        if unicodedata.category(char) == "Nd":
            digit_count += 1
        if char.isspace():
            whitespace_count += 1

    suspicious_char_count = (
        replacement_char_count + private_use_char_count + control_char_count
    )
    denominator = total_chars or 1
    return {
        "total_chars": total_chars,
        "replacement_char_count": replacement_char_count,
        "replacement_char_rate": replacement_char_count / denominator
        if total_chars
        else 0.0,
        "private_use_char_count": private_use_char_count,
        "private_use_char_rate": private_use_char_count / denominator
        if total_chars
        else 0.0,
        "control_char_count": control_char_count,
        "control_char_rate": control_char_count / denominator if total_chars else 0.0,
        "printable_char_count": printable_char_count,
        "printable_char_ratio": printable_char_count / denominator if total_chars else 0.0,
        "ascii_letter_count": ascii_letter_count,
        "cjk_char_count": cjk_char_count,
        "digit_count": digit_count,
        "whitespace_count": whitespace_count,
        "whitespace_ratio": whitespace_count / denominator if total_chars else 0.0,
        "suspicious_char_count": suspicious_char_count,
        "suspicious_char_rate": suspicious_char_count / denominator
        if total_chars
        else 0.0,
    }


@dataclass(frozen=True)
class ThresholdRule:
    """One deterministic one-sided threshold rule."""

    signal_name: str
    operator: str
    threshold: float

    def __post_init__(self) -> None:
        if self.signal_name not in ROUTING_SIGNAL_FIELDS:
            raise ValueError(f"unsupported routing signal: {self.signal_name}")
        if self.operator not in {">=", "<="}:
            raise ValueError("operator must be '>=' or '<='")
        expected = self.signal_name in _GE_SIGNALS if self.operator == ">=" else self.signal_name in _LE_SIGNALS
        if not expected:
            raise ValueError(
                f"operator {self.operator} is not allowed for {self.signal_name}"
            )
        if not isinstance(self.threshold, (int, float)) or isinstance(self.threshold, bool):
            raise TypeError("threshold must be numeric")
        if not math.isfinite(float(self.threshold)):
            raise ValueError("threshold must be finite")

    @property
    def formula(self) -> str:
        return f"{self.signal_name} {self.operator} {self.threshold:.17g}"

    def matches(self, row: Mapping[str, Any]) -> bool:
        value = row.get(self.signal_name)
        if value is None:
            return False
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{self.signal_name} must be numeric or None")
        if self.operator == ">=":
            return float(value) >= float(self.threshold)
        return float(value) <= float(self.threshold)


@dataclass(frozen=True)
class OrRule:
    """A deliberately limited two-signal OR rule."""

    left: ThresholdRule
    right: ThresholdRule

    def __post_init__(self) -> None:
        if self.left.signal_name == self.right.signal_name:
            raise ValueError("two-signal OR rule requires distinct signals")

    @property
    def formula(self) -> str:
        return f"{self.left.formula} OR {self.right.formula}"

    def matches(self, row: Mapping[str, Any]) -> bool:
        return self.left.matches(row) or self.right.matches(row)


TriggerRule = ThresholdRule | OrRule


def threshold_candidates(
    rows: Sequence[Mapping[str, Any]], signal_name: str, operator: str
) -> tuple[float, ...]:
    """Return a finite, deterministic threshold grid from observed review values."""

    if signal_name not in ROUTING_SIGNAL_FIELDS:
        raise ValueError(f"unsupported routing signal: {signal_name}")
    if operator not in {">=", "<="}:
        raise ValueError("operator must be '>=' or '<='")
    if (operator == ">=" and signal_name not in _GE_SIGNALS) or (
        operator == "<=" and signal_name not in _LE_SIGNALS
    ):
        raise ValueError(f"operator {operator} is not allowed for {signal_name}")
    values = {
        float(row[signal_name])
        for row in rows
        if row.get(signal_name) is not None
    }
    return tuple(sorted(values))


def evaluate_trigger(
    rows: Sequence[Mapping[str, Any]],
    rule: TriggerRule,
    *,
    positive_ids: set[str],
    negative_ids: set[str],
    id_field: str = "calibration_item_id",
    main_pool_name: str = "main",
) -> dict[str, Any]:
    """Evaluate a routing rule against reviewed references and Main Sample rows."""

    if positive_ids & negative_ids:
        raise ValueError("positive and negative reference IDs must be disjoint")
    reviewed_ids = positive_ids | negative_ids
    triggered_rows = [row for row in rows if rule.matches(row)]
    reviewed_triggered = [
        row for row in triggered_rows if row.get(id_field) in reviewed_ids
    ]
    true_positive_count = sum(
        row.get(id_field) in positive_ids for row in reviewed_triggered
    )
    false_positive_count = sum(
        row.get(id_field) in negative_ids for row in reviewed_triggered
    )
    main_rows = [row for row in rows if row.get("pool_name") == main_pool_name]
    main_triggered_count = sum(rule.matches(row) for row in main_rows)
    positive_count = len(positive_ids)
    return {
        "trigger": rule.formula,
        "garbled_recall": true_positive_count / positive_count
        if positive_count
        else 0.0,
        "garbled_triggered_count": true_positive_count,
        "garbled_reference_count": positive_count,
        "reviewed_false_positive_count": false_positive_count,
        "reviewed_negative_count": len(negative_ids),
        "reviewed_triggered_count": len(reviewed_triggered),
        "main_triggered_count": main_triggered_count,
        "main_count": len(main_rows),
        "main_triggered_rate": main_triggered_count / len(main_rows)
        if main_rows
        else 0.0,
    }
