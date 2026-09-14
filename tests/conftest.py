"""Shared fixtures for local synthetic/tiny PDF tests."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Callable

import pytest


@pytest.fixture
def make_pdf() -> Callable[[Path, Sequence[str | None]], Path]:
    """Create a tiny PDF fixture without touching the real Source Corpus."""

    def _make_pdf(path: Path, pages: Sequence[str | None]) -> Path:
        import fitz

        path.parent.mkdir(parents=True, exist_ok=True)
        document = fitz.open()
        try:
            for page_text in pages:
                page = document.new_page()
                if page_text:
                    page.insert_text((72, 72), page_text)
            document.save(path)
        finally:
            document.close()
        return path

    return _make_pdf


@pytest.fixture
def long_text() -> str:
    return "机械工业通用知识测试文本。" * 12
