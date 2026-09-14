"""Deterministic D1, D2, and D3 sampling."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import TypeVar

from .discovery import DiscoveredFile
from .identity import file_instance_id


D1_SAMPLING_METHOD = "first_by_sorted_relative_path_per_parent_group"
D2_SAMPLING_METHOD = (
    "evenly_spaced_sorted_relative_path_per_parent_group_excluding_d1"
)
D2_TARGET_PER_GROUP = 10
D3_SAMPLING_METHOD = "proportional_parent_group_evenly_spaced_v0.1"
D3_TARGET_SAMPLE_COUNT = 1000
D3_BASE_QUOTA = 5

GroupKey = tuple[str, str]
KeyT = TypeVar("KeyT")


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


@dataclass(frozen=True)
class D3GroupQuota:
    """Deterministic quota accounting for one source-root/parent-group pair."""

    source_root_id: str
    parent_group: str
    remaining_population: int
    base_quota: int
    proportional_quota: int
    final_quota: int
    largest_remainder_award: int = 0


@dataclass(frozen=True)
class D3Sample:
    items: tuple[DiscoveredFile, ...]
    group_count: int
    target_sample_count: int
    actual_sample_count: int
    excluded_prior_item_count: int
    per_group: tuple[D3GroupQuota, ...]
    sampling_method: str = D3_SAMPLING_METHOD


@dataclass(frozen=True)
class D3QuotaAllocation:
    """Result of the D3 minimum-coverage plus Hamilton allocation."""

    target_sample_count: int
    actual_sample_count: int
    quotas: tuple[D3GroupQuota, ...]


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


def hamilton_allocate(
    capacities: Mapping[KeyT, int],
    target: int,
) -> tuple[dict[KeyT, int], dict[KeyT, int], dict[KeyT, Fraction]]:
    """Allocate an integer target by capacity using deterministic Hamilton rounding.

    The returned values are ``(final_allocation, floors, remainders)``.  Keys are
    ordered by their natural ordering for tie-breaking, so the result does not
    depend on mapping insertion order.  A capacity is the maximum number that
    can be allocated to that key.
    """

    if target < 0:
        raise ValueError("target cannot be negative")
    normalized: dict[KeyT, int] = {}
    for key, capacity in capacities.items():
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise ValueError("capacity must be an integer")
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        normalized[key] = capacity

    total_capacity = sum(normalized.values())
    actual_target = min(target, total_capacity)
    if total_capacity == 0 or actual_target == 0:
        zeros = {key: 0 for key in normalized}
        return zeros, zeros.copy(), {key: Fraction(0, 1) for key in normalized}

    floors: dict[KeyT, int] = {}
    remainders: dict[KeyT, Fraction] = {}
    for key in sorted(normalized):
        numerator = actual_target * normalized[key]
        floors[key] = numerator // total_capacity
        remainders[key] = Fraction(numerator % total_capacity, total_capacity)

    allocation = floors.copy()
    remainder_units = actual_target - sum(floors.values())
    ranked_keys = sorted(
        normalized,
        key=lambda key: (-remainders[key], key),
    )
    for key in ranked_keys[:remainder_units]:
        allocation[key] += 1

    if any(allocation[key] > normalized[key] for key in normalized):  # pragma: no cover
        raise AssertionError("Hamilton allocation exceeded capacity")
    return allocation, floors, remainders


def allocate_d3_quotas(
    remaining_counts: Mapping[GroupKey, int],
    target: int = D3_TARGET_SAMPLE_COUNT,
    base_quota: int = D3_BASE_QUOTA,
) -> D3QuotaAllocation:
    """Allocate D3 quotas with minimum coverage and proportional remainders.

    ``remaining_counts`` must contain only groups with a non-negative remaining
    population. Empty groups are retained in the input but receive no quota.
    When the target exceeds the available population, the actual target is the
    available population and every eligible file is selected.  A target smaller
    than the required minimum coverage is rejected because it cannot satisfy
    the D3 contract for every non-empty group.
    """

    if isinstance(target, bool) or not isinstance(target, int) or target < 0:
        raise ValueError("target must be a non-negative integer")
    if isinstance(base_quota, bool) or not isinstance(base_quota, int) or base_quota < 1:
        raise ValueError("base_quota must be a positive integer")

    normalized = dict(sorted(remaining_counts.items()))
    for key, count in normalized.items():
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"remaining population for {key!r} must be a non-negative integer")

    non_empty = {
        key: count for key, count in normalized.items() if count > 0
    }
    available = sum(non_empty.values())
    actual_target = min(target, available)
    base_by_group = {
        key: min(base_quota, count) for key, count in non_empty.items()
    }
    base_total = sum(base_by_group.values())
    if actual_target < base_total:
        raise ValueError(
            "target is smaller than the required minimum coverage quota "
            f"({actual_target} < {base_total})"
        )

    capacities = {
        key: non_empty[key] - base_by_group[key] for key in non_empty
    }
    extra_target = actual_target - base_total
    extra_allocation, extra_floors, remainders = hamilton_allocate(capacities, extra_target)

    quotas = tuple(
        D3GroupQuota(
            source_root_id=key[0],
            parent_group=key[1],
            remaining_population=non_empty[key],
            base_quota=base_by_group[key],
            proportional_quota=extra_floors[key],
            final_quota=base_by_group[key] + extra_allocation[key],
            largest_remainder_award=extra_allocation[key] - extra_floors[key],
        )
        for key in sorted(non_empty)
    )
    if sum(quota.final_quota for quota in quotas) != actual_target:  # pragma: no cover
        raise AssertionError("D3 quota allocation does not sum to the actual target")
    if any(
        quota.final_quota > quota.remaining_population for quota in quotas
    ):  # pragma: no cover
        raise AssertionError("D3 quota allocation exceeded group population")
    # Evaluate the remainders so a future refactor cannot accidentally discard
    # the deterministic tie-breaking calculation while retaining only floors.
    if set(remainders) != set(capacities):  # pragma: no cover
        raise AssertionError("D3 remainder accounting is incomplete")
    return D3QuotaAllocation(
        target_sample_count=target,
        actual_sample_count=actual_target,
        quotas=quotas,
    )


def select_d3(
    files: list[DiscoveredFile],
    excluded_file_instance_ids: set[str] | frozenset[str],
    target_sample_count: int = D3_TARGET_SAMPLE_COUNT,
    base_quota: int = D3_BASE_QUOTA,
) -> D3Sample:
    """Select a deterministic proportional sample after prior-run exclusions."""

    all_ids: set[str] = set()
    groups: dict[GroupKey, list[DiscoveredFile]] = {}
    for item in files:
        item_id = file_instance_id(item.source_root_id, item.relative_path)
        if item_id in all_ids:
            raise ValueError(f"duplicate File Instance in discovered input: {item_id}")
        all_ids.add(item_id)
        if item_id in excluded_file_instance_ids:
            continue
        groups.setdefault((item.source_root_id, item.parent_group), []).append(item)

    remaining_counts = {
        key: len(candidates) for key, candidates in groups.items()
    }
    allocation = allocate_d3_quotas(
        remaining_counts,
        target=target_sample_count,
        base_quota=base_quota,
    )
    selected: list[DiscoveredFile] = []
    for quota in allocation.quotas:
        key = (quota.source_root_id, quota.parent_group)
        candidates = sorted(groups[key], key=lambda item: item.relative_path)
        indexes = evenly_spaced_indices(len(candidates), quota.final_quota)
        selected.extend(candidates[index] for index in indexes)

    selected.sort(key=lambda item: (item.source_root_id, item.parent_group, item.relative_path))
    selected_ids = [file_instance_id(item.source_root_id, item.relative_path) for item in selected]
    if len(selected_ids) != len(set(selected_ids)):  # pragma: no cover
        raise AssertionError("D3 selected duplicate File Instance")
    return D3Sample(
        items=tuple(selected),
        group_count=len(groups),
        target_sample_count=allocation.target_sample_count,
        actual_sample_count=allocation.actual_sample_count,
        excluded_prior_item_count=len(excluded_file_instance_ids),
        per_group=allocation.quotas,
    )
