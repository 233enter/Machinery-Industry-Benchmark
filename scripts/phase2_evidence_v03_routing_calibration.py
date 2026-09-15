#!/usr/bin/env python3
"""Calibrate deterministic Evidence v0.3 OCR routing signals.

This diagnostic reads only the existing Phase 2 Parquet/JSONL artifacts. It does
not open Source PDFs, run extraction/OCR, or write to the canonical run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT / "src"))

from migb.phase2.quality_signals import (  # noqa: E402
    QUALITY_SIGNAL_FIELDS,
    ROUTING_SIGNAL_FIELDS,
    OrRule,
    ThresholdRule,
    calculate_quality_signals,
    evaluate_trigger,
    threshold_candidates,
)


QUALITY_SIGNAL_REVISION = "quality-signals-v0.1"
ROUTING_CONTRACT_REVISION = "evidence-v0.3-routing-contract-v0.1"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL line at {path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL line is not an object: {path}:{line_number}")
            rows.append(value)
    return rows


def _read_labels(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict) or not isinstance(raw.get("reviewed_items"), list):
        raise ValueError("routing calibration labels must contain reviewed_items")
    labels = raw["reviewed_items"]
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in labels:
        if not isinstance(item, dict):
            raise ValueError("each reviewed item must be a mapping")
        relative_path = item.get("relative_path")
        sufficiency = item.get("sufficiency")
        quality_labels = item.get("quality_labels")
        if (
            not isinstance(relative_path, str)
            or not relative_path
            or relative_path in seen
            or sufficiency not in {"sufficient", "borderline", "insufficient"}
            or not isinstance(quality_labels, list)
            or not all(isinstance(value, str) for value in quality_labels)
        ):
            raise ValueError(f"invalid reviewed item label: {item!r}")
        seen.add(relative_path)
        normalized.append(
            {
                "relative_path": relative_path,
                "sufficiency": sufficiency,
                "quality_labels": list(quality_labels),
            }
        )
    if len(normalized) != 20:
        raise ValueError(f"expected 20 reviewed items, got {len(normalized)}")
    return normalized


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_inputs(run_directory: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sample_path = run_directory / "calibration_sample.parquet"
    evidence_path = run_directory / "calibration_evidence.jsonl"
    if not run_directory.is_dir() or not sample_path.is_file() or not evidence_path.is_file():
        raise ValueError(f"missing canonical input artifacts under {run_directory}")
    sample_rows = pq.read_table(sample_path).to_pylist()
    evidence_rows = _read_jsonl(evidence_path)
    if len(sample_rows) != len(evidence_rows):
        raise ValueError("sample/evidence row counts differ")
    sample_ids = [row.get("calibration_item_id") for row in sample_rows]
    evidence_ids = [row.get("calibration_item_id") for row in evidence_rows]
    if sample_ids != evidence_ids:
        raise ValueError("sample/evidence item order differs")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("duplicate calibration_item_id in canonical input")
    return sample_rows, evidence_rows


def _signal_schema() -> pa.Schema:
    string_fields = (
        "phase2_run_id",
        "calibration_sample_id",
        "calibration_item_id",
        "file_instance_id",
        "pool_name",
        "relative_path",
        "parent_group",
        "evidence_status",
        "evidence_revision",
        "quality_signal_revision",
    )
    boolean_fields = ("evidence_text_available", "total_chars_matches_canonical")
    integer_fields = (
        "canonical_evidence_char_count",
        "canonical_raw_text_char_count",
        "total_chars",
        "replacement_char_count",
        "private_use_char_count",
        "control_char_count",
        "printable_char_count",
        "ascii_letter_count",
        "cjk_char_count",
        "digit_count",
        "whitespace_count",
        "suspicious_char_count",
    )
    float_fields = (
        "replacement_char_rate",
        "private_use_char_rate",
        "control_char_rate",
        "printable_char_ratio",
        "whitespace_ratio",
        "suspicious_char_rate",
    )
    return pa.schema(
        [
            *[pa.field(name, pa.string(), nullable=True) for name in string_fields],
            *[pa.field(name, pa.bool_(), nullable=True) for name in boolean_fields],
            *[pa.field(name, pa.int64(), nullable=True) for name in integer_fields],
            *[pa.field(name, pa.float64(), nullable=True) for name in float_fields],
        ]
    )


def _build_signal_rows(
    sample_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for sample, evidence in zip(sample_rows, evidence_rows):
        evidence_text = evidence.get("evidence_text")
        if evidence_text is not None and not isinstance(evidence_text, str):
            raise ValueError("evidence_text must be a string or null")
        signal_values: dict[str, Any] = {
            name: None for name in QUALITY_SIGNAL_FIELDS
        }
        if isinstance(evidence_text, str):
            signal_values = calculate_quality_signals(evidence_text)
        canonical_count = evidence.get("evidence_char_count")
        output.append(
            {
                "phase2_run_id": evidence.get("phase2_run_id"),
                "calibration_sample_id": evidence.get("calibration_sample_id"),
                "calibration_item_id": evidence.get("calibration_item_id"),
                "file_instance_id": evidence.get("file_instance_id"),
                "pool_name": evidence.get("pool_name"),
                "relative_path": evidence.get("relative_path"),
                "parent_group": evidence.get("parent_group"),
                "evidence_status": evidence.get("evidence_status"),
                "evidence_revision": evidence.get("evidence_revision"),
                "quality_signal_revision": QUALITY_SIGNAL_REVISION,
                "evidence_text_available": isinstance(evidence_text, str),
                "canonical_evidence_char_count": canonical_count,
                "canonical_raw_text_char_count": evidence.get("raw_text_char_count"),
                "total_chars_matches_canonical": (
                    isinstance(evidence_text, str)
                    and isinstance(canonical_count, int)
                    and signal_values["total_chars"] == canonical_count
                ),
                **signal_values,
            }
        )
    return output


def _attach_review_roles(
    signal_rows: list[dict[str, Any]], labels: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    by_path = {row["relative_path"]: row for row in signal_rows}
    label_by_id: dict[str, dict[str, Any]] = {}
    for label in labels:
        row = by_path.get(label["relative_path"])
        if row is None:
            raise ValueError(f"review label path not found in canonical input: {label['relative_path']}")
        if row.get("pool_name") != "main":
            raise ValueError("all reviewed routing references must be in Main Sample")
        if "garbled" in label["quality_labels"]:
            role = "OCR_REQUIRED_REFERENCE"
        else:
            if label["sufficiency"] != "sufficient":
                raise ValueError("non-garbled reviewed reference must be sufficient")
            role = "OCR_NOT_REQUIRED_REFERENCE"
        label_by_id[row["calibration_item_id"]] = {
            **label,
            "calibration_item_id": row["calibration_item_id"],
            "reference_role": role,
        }
    if len(label_by_id) != 20:
        raise ValueError("review labels did not resolve to 20 unique Main items")
    return label_by_id


def _review_rows(
    signal_rows: list[dict[str, Any]], labels_by_id: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    positive_ids = {
        item_id
        for item_id, label in labels_by_id.items()
        if label["reference_role"] == "OCR_REQUIRED_REFERENCE"
    }
    negative_ids = {
        item_id
        for item_id, label in labels_by_id.items()
        if label["reference_role"] == "OCR_NOT_REQUIRED_REFERENCE"
    }
    review = [
        row for row in signal_rows if row.get("calibration_item_id") in labels_by_id
    ]
    if len(positive_ids) != 4 or len(negative_ids) != 16 or len(review) != 20:
        raise ValueError("review reference accounting is not 4 positive / 16 negative / 20 total")
    return review, positive_ids, negative_ids


def _distribution(rows: Iterable[dict[str, Any]], signal_name: str) -> dict[str, float]:
    values = [row[signal_name] for row in rows if row.get(signal_name) is not None]
    if not values:
        return {"min": 0.0, "median": 0.0, "max": 0.0}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def _rank(result: dict[str, Any]) -> tuple[Any, ...]:
    recall = float(result["garbled_recall"])
    return (
        0 if math.isclose(recall, 1.0) else 1,
        result["main_triggered_count"] if math.isclose(recall, 1.0) else -recall,
        result["reviewed_false_positive_count"],
        result["trigger"],
    )


def _best(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        raise ValueError("no trigger candidates were generated")
    return dict(sorted(results, key=_rank)[0])


def _candidate_results(
    signal_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    positive_ids: set[str],
    negative_ids: set[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    best_by_signal: dict[str, dict[str, Any]] = {}
    all_threshold_rules: list[ThresholdRule] = []
    for signal_name in ROUTING_SIGNAL_FIELDS:
        operator = "<=" if signal_name == "printable_char_ratio" else ">="
        rules = [
            ThresholdRule(signal_name, operator, threshold)
            for threshold in threshold_candidates(review_rows, signal_name, operator)
        ]
        all_threshold_rules.extend(rules)
        results = [
            evaluate_trigger(
                signal_rows,
                rule,
                positive_ids=positive_ids,
                negative_ids=negative_ids,
            )
            for rule in rules
        ]
        best_by_signal[signal_name] = _best(results)

    or_results: list[dict[str, Any]] = []
    for index, left in enumerate(all_threshold_rules):
        for right in all_threshold_rules[index + 1 :]:
            if left.signal_name == right.signal_name:
                continue
            rule = OrRule(left, right)
            or_results.append(
                evaluate_trigger(
                    signal_rows,
                    rule,
                    positive_ids=positive_ids,
                    negative_ids=negative_ids,
                )
            )
    return best_by_signal, _best(or_results), or_results


def _write_signal_artifact(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=_signal_schema())
    pq.write_table(table, output_path)


def calibrate(run_directory: Path, labels_path: Path, output_path: Path) -> dict[str, Any]:
    run_directory = run_directory.resolve()
    output_path = output_path.resolve()
    if output_path == run_directory or run_directory in output_path.parents:
        raise ValueError("diagnostic output must not be inside the canonical run directory")
    sample_rows, evidence_rows = _validate_inputs(run_directory)
    labels = _read_labels(labels_path)
    signal_rows = _build_signal_rows(sample_rows, evidence_rows)
    labels_by_id = _attach_review_roles(signal_rows, labels)
    review_rows, positive_ids, negative_ids = _review_rows(signal_rows, labels_by_id)
    _write_signal_artifact(signal_rows, output_path)

    distributions = {
        signal_name: {
            "garbled": _distribution(
                [row for row in review_rows if row["calibration_item_id"] in positive_ids],
                signal_name,
            ),
            "non_garbled": _distribution(
                [row for row in review_rows if row["calibration_item_id"] in negative_ids],
                signal_name,
            ),
        }
        for signal_name in ROUTING_SIGNAL_FIELDS
    }
    best_by_signal, best_or, all_or_results = _candidate_results(
        signal_rows, review_rows, positive_ids, negative_ids
    )
    best_single = _best(list(best_by_signal.values()))
    acceptable = math.isclose(best_single["garbled_recall"], 1.0) and (
        best_single["main_triggered_rate"] <= 0.15
    )
    selected_strategy = "automatic_pre_annotation_ocr" if acceptable else "annotation_side_retry"
    return {
        "quality_signal_revision": QUALITY_SIGNAL_REVISION,
        "routing_contract_revision": ROUTING_CONTRACT_REVISION,
        "input_run_directory": str(run_directory),
        "input_artifact_rows": len(signal_rows),
        "evidence_text_available_rows": sum(
            row["evidence_text_available"] for row in signal_rows
        ),
        "evidence_text_unavailable_rows": sum(
            not row["evidence_text_available"] for row in signal_rows
        ),
        "input_artifact_checksums": {
            name: {
                "size_bytes": (run_directory / name).stat().st_size,
                "sha256": _sha256(run_directory / name),
            }
            for name in ("calibration_sample.parquet", "calibration_evidence.jsonl")
        },
        "output_artifact": {
            "path": str(output_path),
            "row_count": len(signal_rows),
            "size_bytes": output_path.stat().st_size,
            "sha256": _sha256(output_path),
        },
        "reviewed_garbled_count": len(positive_ids),
        "reviewed_non_garbled_count": len(negative_ids),
        "reviewed_reference_role_counts": {
            "OCR_REQUIRED_REFERENCE": len(positive_ids),
            "OCR_NOT_REQUIRED_REFERENCE": len(negative_ids),
        },
        "signal_distributions": distributions,
        "best_single_by_signal": best_by_signal,
        "best_single": best_single,
        "best_two_signal_or": best_or,
        "two_signal_or_candidate_count": len(all_or_results),
        "routing_budget_guideline": {"preferred_max_rate": 0.15, "better_rate": 0.10},
        "automatic_trigger_frozen": acceptable,
        "selected_routing_strategy": selected_strategy,
        "full_767_runtime_authorized": acceptable,
        "text_absent_handling": "excluded from encoding-risk trigger; independent text_absent routing",
        "source_quality_exception_handling": "not_applicable; excluded from encoding-risk trigger",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = calibrate(args.run_dir, args.labels, args.output)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        print(f"Routing calibration failed safely: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
