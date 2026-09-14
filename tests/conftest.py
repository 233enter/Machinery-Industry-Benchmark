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


@pytest.fixture
def make_zero_page_pdf() -> Callable[[Path], Path]:
    """Write a structurally openable PDF whose page tree has zero pages."""

    def _make_zero_page_pdf(path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [] /Count 0 >>",
        ]
        data = b"%PDF-1.4\n"
        offsets = [0]
        for object_number, body in enumerate(objects, start=1):
            offsets.append(len(data))
            data += f"{object_number} 0 obj\n".encode("ascii")
            data += body + b"\nendobj\n"
        xref_offset = len(data)
        data += b"xref\n0 3\n0000000000 65535 f \n"
        data += b"".join(
            f"{offset:010d} 00000 n \n".encode("ascii")
            for offset in offsets[1:]
        )
        data += (
            b"trailer\n<< /Root 1 0 R /Size 3 >>\nstartxref\n"
            + str(xref_offset).encode("ascii")
            + b"\n%%EOF\n"
        )
        path.write_bytes(data)
        return path

    return _make_zero_page_pdf
