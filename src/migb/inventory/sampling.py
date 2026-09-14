"""Deterministic D1 and D2 sampling."""

from __future__ import annotations

from dataclasses import dataclass

from .discovery import DiscoveredFile
from .identity import file_instance_id


D1_SAMPLING_METHOD = "first_by_sorted_relative_path_per_parent_group"
D2_SAMPLING_METHOD = (
    "evenly_spaced_sorted_relative_path_per_parent_group_excluding_d1"
)
D2_TARGET_PER_GROUP = 10


@dataclass(frozen=True)
class D1Sample:
    items: tuple[DiscoveredFile, ...]
    group_count: int
    sampling_method: str = D1_SAMPLING_METHOD


@dataclass(frozen=True)
class D2Sample:
    items: tuple[DiscoveredFile, ...]
    group_count: int
    target_per_group: int
    target_sample_count: int
    actual_sample_count: int
    per_group_sample_count: tuple[tuple[str, str, int], ...]
    sampling_method: str = D2_SAMPLING_METHOD


def select_d1(files: list[DiscoveredFile]) -> D1Sample:
    """Select the first eligible PDF by sorted relative path per source group."""

    groups: dict[tuple[str, str], list[DiscoveredFile]] = {}
    for item in files:
        groups.setdefault((item.source_root_id, item.parent_group), []).append(item)

    selected: list[DiscoveredFile] = []
    for key in sorted(groups):
        candidates = sorted(groups[key], key=lambda item: item.relative_path)
        if candidates:
            selected.append(candidates[0])

    selected.sort(key=lambda item: (item.source_root_id, item.parent_group, item.relative_path))
    return D1Sample(items=tuple(selected), group_count=len(groups))


def evenly_spaced_indices(count: int, target: int) -> tuple[int, ...]:
    """Return deterministic, inclusive, evenly-spaced indexes without randomness."""

    if count < 0:
        raise ValueError("count cannot be negative")
    if target < 1:
        raise ValueError("target must be positive")
    if count == 0:
        return ()
    if count <= target:
        return tuple(range(count))
    if target == 1:
        return (0,)

    denominator = target - 1
    last_index = count - 1
    indexes = tuple(
        (position * last_index + denominator // 2) // denominator
        for position in range(target)
    )
    return tuple(dict.fromkeys(indexes))


def select_d2(
    files: list[DiscoveredFile],
    excluded_file_instance_ids: set[str] | frozenset[str],
    target_per_group: int = D2_TARGET_PER_GROUP,
) -> D2Sample:
    """Sample each group across its sorted path range after excluding D1 items."""

    if target_per_group < 1:
        raise ValueError("target_per_group must be positive")

    groups: dict[tuple[str, str], list[DiscoveredFile]] = {}
    for item in files:
        groups.setdefault((item.source_root_id, item.parent_group), []).append(item)

    selected: list[DiscoveredFile] = []
    per_group_counts: list[tuple[str, str, int]] = []
    for source_root_id, parent_group in sorted(groups):
        candidates = sorted(
            (
                item
                for item in groups[(source_root_id, parent_group)]
                if file_instance_id(item.source_root_id, item.relative_path)
                not in excluded_file_instance_ids
            ),
            key=lambda item: item.relative_path,
        )
        indexes = evenly_spaced_indices(len(candidates), target_per_group)
        selected.extend(candidates[index] for index in indexes)
        per_group_counts.append((source_root_id, parent_group, len(indexes)))

    selected.sort(key=lambda item: (item.source_root_id, item.parent_group, item.relative_path))
    group_count = len(groups)
    return D2Sample(
        items=tuple(selected),
        group_count=group_count,
        target_per_group=target_per_group,
        target_sample_count=group_count * target_per_group,
        actual_sample_count=len(selected),
        per_group_sample_count=tuple(per_group_counts),
    )
