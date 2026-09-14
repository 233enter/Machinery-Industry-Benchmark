from __future__ import annotations

from pathlib import Path

from migb.inventory.discovery import discover_pdfs
from migb.inventory.sampling import D1_SAMPLING_METHOD, select_d1


def test_discovery_preserves_special_names_and_only_finds_regular_pdfs(tmp_path: Path) -> None:
    root = tmp_path / "source"
    (root / "alpha").mkdir(parents=True)
    (root / "beta").mkdir()
    (root / "alpha" / "a.pdf").write_bytes(b"a")
    (root / "alpha" / "notes.txt").write_text("not a PDF", encoding="utf-8")
    (root / "beta" / "中文\n文件.PDF").write_bytes(b"b")

    discovered = discover_pdfs("cmes_journal", root)
    relative_paths = {item.relative_path for item in discovered}

    assert relative_paths == {"alpha/a.pdf", "beta/中文\n文件.PDF"}
    assert {item.parent_group for item in discovered} == {"alpha", "beta"}
    assert all(item.extension.lower() == ".pdf" for item in discovered)


def test_d1_sampling_takes_first_sorted_relative_path_per_group(tmp_path: Path) -> None:
    root = tmp_path / "source"
    (root / "group-a").mkdir(parents=True)
    (root / "group-b").mkdir()
    for relative_path in (
        "group-a/z-last.pdf",
        "group-a/a-first.pdf",
        "group-b/z-last.pdf",
        "group-b/middle.pdf",
    ):
        (root / relative_path).write_bytes(relative_path.encode())

    sample = select_d1(discover_pdfs("cmes_journal", root))

    assert sample.sampling_method == D1_SAMPLING_METHOD
    assert sample.group_count == 2
    assert [item.relative_path for item in sample.items] == [
        "group-a/a-first.pdf",
        "group-b/middle.pdf",
    ]
