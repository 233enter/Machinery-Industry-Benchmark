from __future__ import annotations

from pathlib import Path

from migb.inventory.discovery import DiscoveredFile
from migb.inventory.identity import file_instance_id
from migb.inventory.sampling import (
    D2_SAMPLING_METHOD,
    evenly_spaced_indices,
    select_d2,
)


def _discovered(relative_path: str, parent_group: str = "group") -> DiscoveredFile:
    path = Path("/synthetic") / relative_path
    return DiscoveredFile(
        source_root_id="cmes_journal",
        path=path,
        relative_path=relative_path,
        file_name=path.name,
        parent_group=parent_group,
        extension=path.suffix,
    )


def test_evenly_spaced_indices_handles_ten_more_than_ten_and_small_groups() -> None:
    assert evenly_spaced_indices(10, 10) == tuple(range(10))
    assert evenly_spaced_indices(20, 10) == (0, 2, 4, 6, 8, 11, 13, 15, 17, 19)
    assert evenly_spaced_indices(4, 10) == (0, 1, 2, 3)


def test_d2_excludes_d1_items_and_is_deterministic() -> None:
    files = [_discovered(f"group/item-{index:02d}.pdf") for index in range(12)]
    excluded = {
        file_instance_id("cmes_journal", "group/item-00.pdf"),
        file_instance_id("cmes_journal", "group/item-06.pdf"),
    }

    first = select_d2(files, excluded)
    second = select_d2(list(reversed(files)), excluded)

    assert first == second
    assert first.sampling_method == D2_SAMPLING_METHOD
    assert first.target_sample_count == 10
    assert first.actual_sample_count == 10
    assert [item.relative_path for item in first.items] == [
        f"group/item-{index:02d}.pdf" for index in range(12) if index not in {0, 6}
    ]
    assert not {
        file_instance_id("cmes_journal", item.relative_path) for item in first.items
    } & excluded


def test_d2_sampling_covers_sorted_range_and_preserves_special_paths() -> None:
    files = [
        _discovered("special/a\nline.pdf", "special"),
        _discovered("special/middle.pdf", "special"),
        _discovered("special/z-last.pdf", "special"),
    ]

    sample = select_d2(files, set(), target_per_group=2)

    assert [item.relative_path for item in sample.items] == [
        "special/a\nline.pdf",
        "special/z-last.pdf",
    ]
    assert sample.per_group_sample_count == (("cmes_journal", "special", 2),)
