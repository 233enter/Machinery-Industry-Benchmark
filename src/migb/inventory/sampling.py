"""Deterministic D1 sampling."""

from __future__ import annotations

from dataclasses import dataclass

from .discovery import DiscoveredFile


D1_SAMPLING_METHOD = "first_by_sorted_relative_path_per_parent_group"


@dataclass(frozen=True)
class D1Sample:
    items: tuple[DiscoveredFile, ...]
    group_count: int
    sampling_method: str = D1_SAMPLING_METHOD


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
