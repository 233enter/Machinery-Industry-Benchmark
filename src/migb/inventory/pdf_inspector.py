"""PyMuPDF-backed lightweight PDF inspection."""

from __future__ import annotations

from typing import Any


def sampled_page_indices(page_count: int) -> tuple[int, ...]:
    """Return legal, de-duplicated first/middle/last page indexes."""

    if page_count <= 0:
        return ()
    candidates = (0, page_count // 2, page_count - 1)
    return tuple(dict.fromkeys(index for index in candidates if 0 <= index < page_count))


def classify_text_layer(
    text_char_counts: list[int],
    extraction_failures: int,
    threshold: int,
) -> str:
    """Apply the frozen D1 text-layer heuristic."""

    if extraction_failures and not text_char_counts:
        return "check_failed"
    if extraction_failures == 0 and text_char_counts and all(count == 0 for count in text_char_counts):
        return "text_absent"
    if (
        extraction_failures == 0
        and text_char_counts
        and all(count >= threshold for count in text_char_counts)
    ):
        return "text_present"
    return "mixed_or_uncertain"


def _error(stage: str, category: str, exc: BaseException) -> dict[str, str]:
    return {
        "stage": stage,
        "error_category": category,
        "error_message": f"{type(exc).__name__}: {exc}",
    }


def _metadata_value(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return None if value is None else str(value)


def inspect_pdf(path: str, text_page_char_threshold: int) -> dict[str, Any]:
    """Open one PDF and collect lightweight metadata and text-layer signals.

    The function imports PyMuPDF inside the worker task so a Document is never
    created in a parent process and shared with another process.
    """

    result: dict[str, Any] = {
        "pdf_open_status": "not_attempted",
        "pdf_error_category": None,
        "pdf_status": "unknown",
        "is_encrypted": None,
        "pdf_version": None,
        "page_count": None,
        "metadata_title": None,
        "metadata_author": None,
        "metadata_subject": None,
        "metadata_keywords": None,
        "metadata_creator": None,
        "metadata_producer": None,
        "metadata_creation_date": None,
        "metadata_modification_date": None,
        "sampled_page_count": 0,
        "sampled_text_char_count": 0,
        "text_layer_status": "check_failed",
        "errors": [],
    }

    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - exercised by environment setup failure
        result["errors"].append(_error("pdf_open", "missing_pdf_library", exc))
        result["pdf_error_category"] = "missing_pdf_library"
        return result

    document = None
    try:
        document = fitz.open(path)
        result["pdf_open_status"] = "success"
    except Exception as exc:
        result["pdf_open_status"] = "failed"
        result["pdf_status"] = "unknown"
        result["pdf_error_category"] = type(exc).__name__
        result["errors"].append(_error("pdf_open", type(exc).__name__, exc))
        return result

    try:
        needs_password = bool(getattr(document, "needs_pass", False))
        result["is_encrypted"] = needs_password
        if needs_password:
            result["pdf_status"] = "encrypted"
            result["text_layer_status"] = "check_failed"
            return result

        result["pdf_status"] = "valid"

        try:
            result["page_count"] = int(document.page_count)
        except Exception as exc:
            result["pdf_error_category"] = type(exc).__name__
            result["errors"].append(_error("metadata", type(exc).__name__, exc))
            return result

        try:
            pdf_version = getattr(document, "pdf_version", None)
            version_value = pdf_version() if callable(pdf_version) else pdf_version
            result["pdf_version"] = None if version_value is None else str(version_value)
        except Exception as exc:
            result["pdf_error_category"] = type(exc).__name__
            result["errors"].append(_error("metadata", "pdf_version_parse", exc))

        try:
            metadata = document.metadata or {}
            for key in (
                "title",
                "author",
                "subject",
                "keywords",
                "creator",
                "producer",
                "creationDate",
                "modDate",
            ):
                if not isinstance(metadata, dict):
                    raise TypeError("PDF metadata is not a mapping")
            result.update(
                {
                    "metadata_title": _metadata_value(metadata, "title"),
                    "metadata_author": _metadata_value(metadata, "author"),
                    "metadata_subject": _metadata_value(metadata, "subject"),
                    "metadata_keywords": _metadata_value(metadata, "keywords"),
                    "metadata_creator": _metadata_value(metadata, "creator"),
                    "metadata_producer": _metadata_value(metadata, "producer"),
                    "metadata_creation_date": _metadata_value(metadata, "creationDate"),
                    "metadata_modification_date": _metadata_value(metadata, "modDate"),
                }
            )
        except Exception as exc:
            result["pdf_error_category"] = type(exc).__name__
            result["errors"].append(_error("metadata", "metadata_parse", exc))

        page_count = result["page_count"]
        if page_count is None or page_count == 0:
            exc = ValueError("PDF has no readable pages")
            result["text_layer_status"] = "check_failed"
            result["errors"].append(_error("text_sample", "zero_page_count", exc))
            return result

        counts: list[int] = []
        extraction_failures = 0
        for page_index in sampled_page_indices(page_count):
            result["sampled_page_count"] += 1
            try:
                page = document.load_page(page_index)
                text = page.get_text()
                counts.append(len(text.strip()))
            except Exception as exc:
                extraction_failures += 1
                result["errors"].append(_error("text_sample", type(exc).__name__, exc))

        result["sampled_text_char_count"] = sum(counts)
        result["text_layer_status"] = classify_text_layer(
            counts,
            extraction_failures,
            text_page_char_threshold,
        )
    finally:
        if document is not None:
            document.close()
    return result
