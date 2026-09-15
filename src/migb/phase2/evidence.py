"""PyMuPDF lightweight Evidence extraction for the Gate 2B selection bundle."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any


EVIDENCE_REVISION = "evidence-v0.1-gate2b"
PAGE_DELIMITER_TEMPLATE = "<<<PAGE:{page_index}>>>\n"


def normalize_page_text(value: str) -> str:
    """Apply only the frozen line-ending normalization."""

    return value.replace("\r\n", "\n").replace("\r", "\n")


def assemble_evidence(
    page_texts: list[tuple[int, str]],
    max_extracted_chars: int,
) -> tuple[str, int, bool, int]:
    """Assemble page text with stable delimiters and apply the exact cap."""

    if max_extracted_chars < 1:
        raise ValueError("max_extracted_chars must be positive")
    parts = [
        PAGE_DELIMITER_TEMPLATE.format(page_index=page_index) + text
        for page_index, text in page_texts
    ]
    assembled = "\n".join(parts)
    raw_text_char_count = sum(len(text) for _, text in page_texts)
    truncated = len(assembled) > max_extracted_chars
    return assembled[:max_extracted_chars], len(assembled[:max_extracted_chars]), truncated, raw_text_char_count


def _base_evidence_row(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "phase2_run_id": task["phase2_run_id"],
        "calibration_sample_id": task["calibration_sample_id"],
        "calibration_item_id": task["calibration_item_id"],
        "file_instance_id": task["file_instance_id"],
        "pool_name": task["pool_name"],
        "relative_path": task["relative_path"],
        "parent_group": task["parent_group"],
        "sha256": task.get("sha256"),
        "page_count": task.get("page_count"),
        "text_layer_status": task.get("text_layer_status"),
        "filename_title": task.get("filename_title"),
        "metadata_title": task.get("metadata_title"),
        "evidence_text": None,
        "evidence_page_indices": [],
        "evidence_char_count": 0,
        "raw_text_char_count": 0,
        "evidence_truncated": False,
        "evidence_status": "failed",
        "evidence_error_stage": None,
        "evidence_error_type": None,
        "evidence_error_message": None,
        "source_size_before": None,
        "source_mtime_ns_before": None,
        "source_size_after": None,
        "source_mtime_ns_after": None,
        "source_changed_during_evidence": False,
        "evidence_revision": task.get("evidence_revision", EVIDENCE_REVISION),
    }


def _stat_tuple(path: Path) -> tuple[int, int]:
    stat_result = path.stat()
    return stat_result.st_size, stat_result.st_mtime_ns


def _set_error(row: dict[str, Any], stage: str, exc: BaseException) -> None:
    row["evidence_error_stage"] = stage
    row["evidence_error_type"] = type(exc).__name__
    row["evidence_error_message"] = f"{type(exc).__name__}: {exc}"


def extract_evidence_task(task: dict[str, Any]) -> dict[str, Any]:
    """Extract one Evidence record in a process that owns its PyMuPDF handle."""

    row = _base_evidence_row(task)
    path = Path(task["source_path"])
    expected_size = task.get("expected_size_bytes")
    expected_mtime = task.get("expected_mtime_ns")

    try:
        before_size, before_mtime = _stat_tuple(path)
        row["source_size_before"] = before_size
        row["source_mtime_ns_before"] = before_mtime
    except OSError as exc:
        _set_error(row, "stat_before", exc)
        return row

    if (
        expected_size is not None
        and expected_mtime is not None
        and (before_size != expected_size or before_mtime != expected_mtime)
    ):
        row["source_changed_during_evidence"] = True
        _set_error(row, "source_consistency", RuntimeError("source differs from Full Inventory"))
        try:
            after_size, after_mtime = _stat_tuple(path)
            row["source_size_after"] = after_size
            row["source_mtime_ns_after"] = after_mtime
        except OSError:
            pass
        return row

    if task.get("not_applicable") is True:
        row["evidence_status"] = "not_applicable"
        try:
            after_size, after_mtime = _stat_tuple(path)
            row["source_size_after"] = after_size
            row["source_mtime_ns_after"] = after_mtime
            row["source_changed_during_evidence"] = (
                before_size != after_size or before_mtime != after_mtime
            )
        except OSError as exc:
            row["source_changed_during_evidence"] = True
            _set_error(row, "source_consistency", exc)
        return row

    document = None
    try:
        import fitz

        document = fitz.open(path.as_posix())
        actual_page_count = int(document.page_count)
        expected_page_count = task.get("page_count")
        page_count_mismatch = (
            isinstance(expected_page_count, int)
            and actual_page_count != expected_page_count
        )
        if page_count_mismatch:
            _set_error(
                row,
                "page_count_validation",
                RuntimeError(
                    f"page count changed from {expected_page_count} to {actual_page_count}"
                ),
            )
        else:
            intended_indices = [
                index
                for index in task.get("page_indices", [0, 1, 2])
                if index < actual_page_count
            ]
            page_texts: list[tuple[int, str]] = []
            failures: list[BaseException] = []
            for page_index in intended_indices:
                try:
                    page = document.load_page(page_index)
                    page_texts.append(
                        (page_index, normalize_page_text(page.get_text("text")))
                    )
                except Exception as exc:  # PyMuPDF may use multiple exception classes here.
                    failures.append(exc)

            evidence_text, evidence_char_count, truncated, raw_text_char_count = (
                assemble_evidence(
                    page_texts,
                    int(task["max_extracted_chars"]),
                )
            )
            row.update(
                {
                    "evidence_text": evidence_text,
                    "evidence_page_indices": [
                        page_index for page_index, _ in page_texts
                    ],
                    "evidence_char_count": evidence_char_count,
                    "raw_text_char_count": raw_text_char_count,
                    "evidence_truncated": truncated,
                }
            )
            if failures:
                _set_error(row, "page_text", failures[0])
                row["evidence_status"] = "partial" if page_texts else "failed"
            else:
                row["evidence_status"] = "success"
    except Exception as exc:
        _set_error(row, "evidence_extraction", exc)
        row["evidence_status"] = "failed"
    finally:
        if document is not None:
            document.close()

    try:
        after_size, after_mtime = _stat_tuple(path)
        row["source_size_after"] = after_size
        row["source_mtime_ns_after"] = after_mtime
        if before_size != after_size or before_mtime != after_mtime:
            row["source_changed_during_evidence"] = True
            if row["evidence_error_stage"] is None:
                _set_error(
                    row,
                    "source_consistency",
                    RuntimeError("size or mtime changed during Evidence extraction"),
                )
    except OSError as exc:
        row["source_changed_during_evidence"] = True
        _set_error(row, "source_consistency", exc)
    return row


def _worker_failure_row(task: dict[str, Any], exc: BaseException) -> dict[str, Any]:
    row = _base_evidence_row(task)
    _set_error(row, "worker", exc)
    return row


def extract_evidence(
    tasks: list[dict[str, Any]],
    *,
    worker_count: int = 4,
) -> list[dict[str, Any]]:
    """Extract Evidence with process-isolated PyMuPDF workers and restore order."""

    if worker_count < 1:
        raise ValueError("worker_count must be positive")
    if not tasks:
        return []
    by_item_id: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        future_to_task = {
            executor.submit(extract_evidence_task, task): task for task in tasks
        }
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            item_id = task["calibration_item_id"]
            if item_id in by_item_id:
                raise ValueError(f"duplicate evidence task: {item_id}")
            try:
                by_item_id[item_id] = future.result()
            except Exception as exc:  # Keep one worker failure visible in the artifact.
                by_item_id[item_id] = _worker_failure_row(task, exc)
    return [by_item_id[task["calibration_item_id"]] for task in tasks]
