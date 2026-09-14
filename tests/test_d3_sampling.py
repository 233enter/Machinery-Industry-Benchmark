from __future__ import annotations

from pathlib import Path

from migb.inventory.discovery import DiscoveredFile
from migb.inventory.identity import file_instance_id
from migb.inventory.sampling import (
    D3_SAMPLING_METHOD,
    allocate_d3_quotas,
    hamilton_allocate,
    select_d3,
)


def _discovered(relative_path: str, parent_group: str) -> DiscoveredFile:
    path = Path("/synthetic") / relative_path
    return DiscoveredFile(
        source_root_id="cmes_journal",
        path=path,
        relative_path=relative_path,
        file_name=path.name,
        parent_group=parent_group,
        extension=path.suffix,
    )


def test_hamilton_allocate_is_deterministic_for_largest_remainder_ties() -> None:
    first, floors, remainders = hamilton_allocate(
        {"c": 1, "a": 1, "b": 1},
        2,
    )
    second, _, _ = hamilton_allocate({"b": 1, "c": 1, "a": 1}, 2)

    assert first == {"a": 1, "b": 1, "c": 0}
    assert second == first
    assert floors == {"a": 0, "b": 0, "c": 0}
    assert remainders["a"] == remainders["b"] == remainders["c"]


def test_d3_quota_allocation_covers_small_empty_and_under_base_groups() -> None:
    allocation = allocate_d3_quotas(
        {
            ("root", "big"): 100,
            ("root", "medium"): 10,
            ("root", "small"): 3,
            ("root", "empty"): 0,
        },
        target=50,
    )

    assert allocation.actual_sample_count == 50
    assert [(quota.parent_group, quota.final_quota) for quota in allocation.quotas] == [
        ("big", 40),
        ("medium", 7),
        ("small", 3),
    ]
    assert all(quota.final_quota <= quota.remaining_population for quota in allocation.quotas)


def test_d3_quota_allocation_records_actual_count_when_population_is_small() -> None:
    allocation = allocate_d3_quotas({("root", "only"): 4, ("root", "empty"): 0}, target=1000)

    assert allocation.target_sample_count == 1000
    assert allocation.actual_sample_count == 4
    assert allocation.quotas[0].base_quota == 4
    assert allocation.quotas[0].final_quota == 4


def test_select_d3_excludes_prior_ids_and_preserves_special_paths_deterministically() -> None:
    files = [
        _discovered("group/a\nline.pdf", "group"),
        _discovered("group/middle.pdf", "group"),
        _discovered("group/z-last.pdf", "group"),
        _discovered("group/extra.pdf", "group"),
        _discovered("other/item-0.pdf", "other"),
        _discovered("other/item-1.pdf", "other"),
        _discovered("other/item-2.pdf", "other"),
        _discovered("other/item-3.pdf", "other"),
    ]
    excluded = {
        file_instance_id("cmes_journal", "group/middle.pdf"),
        file_instance_id("cmes_journal", "other/item-0.pdf"),
    }

    first = select_d3(files, excluded, target_sample_count=6, base_quota=1)
    second = select_d3(list(reversed(files)), excluded, target_sample_count=6, base_quota=1)
    selected_ids = {
        file_instance_id(item.source_root_id, item.relative_path) for item in first.items
    }

    assert first == second
    assert first.sampling_method == D3_SAMPLING_METHOD
    assert first.actual_sample_count == 6
    assert len(first.items) == len(selected_ids) == 6
    assert not selected_ids & excluded
    assert any("\n" in item.relative_path for item in first.items)
