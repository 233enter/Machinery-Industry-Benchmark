"""Optional RapidOCR adapter for the Evidence v0.3 diagnostic path.

The OCR dependency is intentionally imported only inside the functions that
need it.  Inventory, sampling, and the existing PyMuPDF Evidence path can
therefore run without installing the ``ocr`` optional extra.
"""

from __future__ import annotations

import importlib.metadata
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Iterable


OCR_ENGINE = "rapidocr"
OCR_LANGUAGES = "ch+en"
OCR_REVISION = "evidence-v0.3-rapidocr"
DEFAULT_PER_PAGE_CHAR_CAP = 4000
DEFAULT_GLOBAL_CHAR_CAP = 20000


class OCRRuntimeError(RuntimeError):
    """Raised when the optional OCR runtime is unavailable or unusable."""


@dataclass(frozen=True)
class OCRRuntimeInfo:
    """Versions and execution providers used by the optional OCR runtime."""

    rapidocr_version: str
    onnxruntime_version: str
    available_providers: tuple[str, ...]
    execution_provider: str
    languages: str = OCR_LANGUAGES


@dataclass(frozen=True)
class OCRDetection:
    """One OCR detection after stable reading-order normalization."""

    text: str
    score: float | None
    box: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class OCRPageResult:
    """OCR output for one rendered PDF page."""

    page_index: int
    render_dpi: int
    detections: tuple[OCRDetection, ...]
    ocr_runtime_seconds: float

    @property
    def text(self) -> str:
        """Return detections in top-to-bottom, left-to-right reading order."""

        return "\n".join(detection.text for detection in self.detections)


def _distribution_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError as exc:
        raise OCRRuntimeError(f"OCR dependency is not installed: {distribution}") from exc


def inspect_runtime() -> OCRRuntimeInfo:
    """Validate the CPU OCR runtime without instantiating the OCR model."""

    try:
        import onnxruntime
    except ImportError as exc:
        raise OCRRuntimeError(
            "onnxruntime is unavailable; install the optional 'ocr' extra"
        ) from exc

    try:
        import rapidocr  # noqa: F401  # Import check only; loading is lazy below.
    except ImportError as exc:
        raise OCRRuntimeError(
            "rapidocr is unavailable; install the optional 'ocr' extra"
        ) from exc

    providers = tuple(onnxruntime.get_available_providers())
    if "CPUExecutionProvider" not in providers:
        raise OCRRuntimeError(
            "onnxruntime does not provide CPUExecutionProvider: "
            + ", ".join(providers)
        )
    return OCRRuntimeInfo(
        rapidocr_version=_distribution_version("rapidocr"),
        onnxruntime_version=_distribution_version("onnxruntime"),
        available_providers=providers,
        execution_provider="CPUExecutionProvider",
    )


def build_provenance(
    *,
    render_dpi: int,
    selected_page_indices: Iterable[int],
    ocr_raw_char_count: int,
    ocr_stored_char_count: int,
    ocr_runtime_seconds: float,
    runtime: OCRRuntimeInfo | None = None,
) -> dict[str, Any]:
    """Build the minimum provenance record required by Evidence v0.3."""

    if isinstance(render_dpi, bool) or not isinstance(render_dpi, int) or render_dpi < 1:
        raise ValueError("render_dpi must be a positive integer")
    if ocr_raw_char_count < 0 or ocr_stored_char_count < 0:
        raise ValueError("OCR character counts must be non-negative")
    if ocr_runtime_seconds < 0:
        raise ValueError("ocr_runtime_seconds must be non-negative")
    info = runtime or inspect_runtime()
    return {
        "extractor": "pymupdf_render_to_png+rapidocr",
        "ocr_engine": OCR_ENGINE,
        "ocr_engine_version": info.rapidocr_version,
        "ocr_languages": info.languages,
        "render_dpi": render_dpi,
        "selected_page_indices": list(selected_page_indices),
        "ocr_raw_char_count": ocr_raw_char_count,
        "ocr_stored_char_count": ocr_stored_char_count,
        "ocr_runtime_seconds": ocr_runtime_seconds,
        "onnxruntime_version": info.onnxruntime_version,
        "execution_provider": info.execution_provider,
    }


def load_engine() -> Callable[[Any], Any]:
    """Load RapidOCR only when explicitly requested by the OCR path."""

    inspect_runtime()
    try:
        from rapidocr import RapidOCR

        return RapidOCR()
    except Exception as exc:  # Model loading errors vary between RapidOCR versions.
        raise OCRRuntimeError(f"RapidOCR model initialization failed: {exc}") from exc


def select_page_indices(page_count: int) -> list[int]:
    """Return the frozen first-three plus middle/late probe page selector."""

    if isinstance(page_count, bool) or not isinstance(page_count, int):
        raise ValueError("page_count must be an integer")
    if page_count < 1:
        return []
    base = [0, 1, 2]
    middle = math.floor((page_count - 1) * 0.50)
    late = math.floor((page_count - 1) * 0.75)
    return sorted({index for index in base + [middle, late] if index < page_count})


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    try:
        return list(value)
    except TypeError:
        return [value]


def _is_numeric_pair(value: Any) -> bool:
    pair = _as_sequence(value)
    return len(pair) == 2 and all(
        isinstance(component, (int, float)) and not isinstance(component, bool)
        for component in pair
    )


def _normalize_box(value: Any) -> tuple[tuple[float, float], ...]:
    points = _as_sequence(value)
    if _is_numeric_pair(points):
        points = [points]
    normalized: list[tuple[float, float]] = []
    for point in points:
        if not _is_numeric_pair(point):
            continue
        pair = _as_sequence(point)
        normalized.append((float(pair[0]), float(pair[1])))
    return tuple(normalized)


def _result_components(result: Any) -> tuple[Any, Any, Any]:
    """Support RapidOCR result objects and older tuple-style return values."""

    for box_name, text_name, score_name in (
        ("boxes", "txts", "scores"),
        ("boxes", "texts", "scores"),
    ):
        boxes = getattr(result, box_name, None)
        texts = getattr(result, text_name, None)
        scores = getattr(result, score_name, None)
        if boxes is not None or texts is not None or scores is not None:
            return boxes, texts, scores

    if isinstance(result, (tuple, list)):
        if len(result) >= 3:
            return result[0], result[1], result[2]
        if len(result) == 2 and not isinstance(result[0], (str, bytes)):
            nested = _result_components(result[0])
            if any(component is not None for component in nested):
                return nested
    return [], [], []


def normalize_detections(result: Any) -> tuple[OCRDetection, ...]:
    """Normalize RapidOCR output and apply deterministic bbox reading order."""

    boxes_value, texts_value, scores_value = _result_components(result)
    boxes = _as_sequence(boxes_value)
    texts = _as_sequence(texts_value)
    scores = _as_sequence(scores_value)

    # A single polygon may be returned as four points rather than [polygon].
    if boxes and all(_is_numeric_pair(point) for point in boxes):
        boxes = [boxes]

    detection_count = max(len(boxes), len(texts), len(scores))
    detections: list[tuple[int, OCRDetection]] = []
    for index in range(detection_count):
        text_value = texts[index] if index < len(texts) else ""
        text = str(text_value).strip()
        if not text:
            continue
        box = _normalize_box(boxes[index]) if index < len(boxes) else ()
        score: float | None = None
        if index < len(scores) and scores[index] is not None:
            try:
                score = float(scores[index])
            except (TypeError, ValueError):
                score = None
        detections.append((index, OCRDetection(text=text, score=score, box=box)))

    def reading_order(item: tuple[int, OCRDetection]) -> tuple[float, float, int]:
        index, detection = item
        if not detection.box:
            return (float("inf"), float("inf"), index)
        min_x = min(point[0] for point in detection.box)
        min_y = min(point[1] for point in detection.box)
        return (min_y, min_x, index)

    return tuple(detection for _, detection in sorted(detections, key=reading_order))


def ocr_image(image: Any, *, engine: Callable[[Any], Any] | None = None) -> OCRPageResult:
    """Run RapidOCR on an image path/array using a lazily loaded engine."""

    active_engine = engine or load_engine()
    started = perf_counter()
    result = active_engine(image)
    detections = normalize_detections(result)
    return OCRPageResult(
        page_index=-1,
        render_dpi=0,
        detections=detections,
        ocr_runtime_seconds=perf_counter() - started,
    )


def ocr_pdf_page(
    pdf_path: str | Path,
    page_index: int,
    *,
    render_dpi: int,
    engine: Callable[[Any], Any] | None = None,
) -> OCRPageResult:
    """Render one original PDF page to a temporary PNG and OCR that image."""

    if isinstance(page_index, bool) or not isinstance(page_index, int) or page_index < 0:
        raise ValueError("page_index must be a non-negative integer")
    if isinstance(render_dpi, bool) or not isinstance(render_dpi, int) or render_dpi < 1:
        raise ValueError("render_dpi must be a positive integer")

    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - project dependency in normal use
        raise OCRRuntimeError("PyMuPDF is required to render OCR input pages") from exc

    document = None
    try:
        document = fitz.open(Path(pdf_path).as_posix())
        if page_index >= document.page_count:
            raise ValueError(
                f"page_index {page_index} is outside document with "
                f"{document.page_count} pages"
            )
        page = document.load_page(page_index)
        pixmap = page.get_pixmap(dpi=render_dpi, alpha=False)
        with tempfile.TemporaryDirectory(prefix="migb-ocr-") as temp_dir:
            image_path = Path(temp_dir) / f"page-{page_index}.png"
            pixmap.save(image_path.as_posix())
            result = ocr_image(image_path, engine=engine)
        return OCRPageResult(
            page_index=page_index,
            render_dpi=render_dpi,
            detections=result.detections,
            ocr_runtime_seconds=result.ocr_runtime_seconds,
        )
    finally:
        if document is not None:
            document.close()


def assemble_evidence(
    page_results: Iterable[OCRPageResult],
    *,
    per_page_char_cap: int = DEFAULT_PER_PAGE_CHAR_CAP,
    global_char_cap: int = DEFAULT_GLOBAL_CHAR_CAP,
) -> dict[str, Any]:
    """Apply page/global caps while retaining stable page delimiters."""

    if per_page_char_cap < 1 or global_char_cap < 1:
        raise ValueError("character caps must be positive")
    pages = list(page_results)
    page_parts: list[str] = []
    page_metrics: list[dict[str, Any]] = []
    raw_char_count = 0
    runtime_seconds = 0.0
    for page in pages:
        page_text = page.text
        stored_page_text = page_text[:per_page_char_cap]
        raw_char_count += len(page_text)
        runtime_seconds += page.ocr_runtime_seconds
        page_parts.append(f"<<<PAGE:{page.page_index}>>>\n{stored_page_text}")
        page_metrics.append(
            {
                "page_index": page.page_index,
                "raw_char_count": len(page_text),
                "stored_char_count": len(stored_page_text),
                "page_truncated": len(stored_page_text) < len(page_text),
            }
        )

    assembled = "\n".join(page_parts)
    evidence_text = assembled[:global_char_cap]
    return {
        "evidence_text": evidence_text,
        "evidence_page_indices": [page.page_index for page in pages],
        "ocr_raw_char_count": raw_char_count,
        "ocr_stored_char_count": len(evidence_text),
        "evidence_truncated": len(evidence_text) < len(assembled),
        "page_metrics": page_metrics,
        "ocr_runtime_seconds": runtime_seconds,
    }
