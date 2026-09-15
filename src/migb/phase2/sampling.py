"""Deterministic Phase 2 calibration sampling and Audit Pool selection."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Mapping

from migb.inventory.sampling import evenly_spaced_indices, hamilton_allocate


POOL_ORDER = (
    "main",
    "source_quality_exception",
    "text_absent",
    "mixed_text",
    "filename_unmatched",
)
POOL_PRIORITY = {
    pool_name: index for index, pool_name in enumerate(POOL_ORDER)
}

MAIN_SAMPLING_METHOD = "group_base_coverage_hamilton_evenly_spaced_v0.1"
AUDIT_SAMPLING_METHODS = {
    "text_absent": "audit_minimum_coverage_hamilton_evenly_spaced_v0.1",
    "mixed_text": "audit_minimum_coverage_hamilton_evenly_spaced_v0.1",
    "filename_unmatched": "audit_minimum_coverage_hamilton_evenly_spaced_v0.1",
}
EXCEPTION_SAMPLING_METHOD = "source_quality_exception_all_v0.1"


@dataclass(frozen=True)
class DuplicateInfo:
    duplicate_group_id: str
    sha256: str
    representative_file_instance_id: str
    is_representative: bool


@dataclass(frozen=True)
class GroupQuota:
    pool_name: str
    parent_group: str
    population: int
    base_quota: int
    proportional_quota: int
    remainder: Fraction
    largest_remainder_award: int
    final_quota: int
    actual_selected_count: int


@dataclass(frozen=True)
class SampleItem:
    record: dict[str, Any]
    sample_role: str
    pool_name: str
    pool_priority: int
    group_population: int
    group_quota: int
    selection_rank_or_index: int
    sampling_method: str
    duplicate_group_id: str | None
    exact_duplicate_representative: bool


@dataclass(frozen=True)
class PoolSelection:
    pool_name: str
    target: int
    actual_count: int
    candidate_count: int
    group_quotas: tuple[GroupQuota, ...]
    items: tuple[SampleItem, ...]


@dataclass(frozen=True)
class CalibrationSelection:
    items: tuple[SampleItem, ...]
    main_physical_eligible_count: int
    main_duplicate_collapsed_eligible_count: int
    exact_duplicates_excluded_from_sampling: int
    pools: tuple[PoolSelection, ...]
    main_audit_overlap_count: int
    cross_pool_overlap_count: int


def calibration_item_id(calibration_sample_id: str, file_instance_id: str) -> str:
    """Return the frozen UUIDv5 identity for one calibration item."""

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"migb://phase2/calibration-item/{calibration_sample_id}/{file_instance_id}",
        )
    )


def _file_id(record: Mapping[str, Any]) -> str:
    value = record.get("file_instance_id")
    if not isinstance(value, str) or not value:
        raise ValueError("inventory record is missing file_instance_id")
    return value


def _group(record: Mapping[str, Any]) -> str:
    value = record.get("parent_group")
    if not isinstance(value, str):
        raise ValueError("inventory record is missing parent_group")
    return value


def _record_sort_key(record: Mapping[str, Any]) -> tuple[str, str]:
    relative_path = record.get("relative_path")
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("inventory record is missing relative_path")
    return relative_path, _file_id(record)


def build_duplicate_mapping(
    records: Iterable[Mapping[str, Any]],
    duplicate_rows: Iterable[Mapping[str, Any]],
) -> dict[str, DuplicateInfo]:
    """Validate duplicate_groups.parquet and return member-to-group mappings."""

    record_by_id = {_file_id(record): record for record in records}
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in duplicate_rows:
        group_id = row.get("duplicate_group_id")
        file_id = row.get("file_instance_id")
        sha256 = row.get("sha256")
        if not all(isinstance(value, str) and value for value in (group_id, file_id, sha256)):
            raise ValueError("duplicate row has incomplete identity fields")
        if file_id not in record_by_id:
            raise ValueError(f"duplicate row references unknown File Instance: {file_id}")
        if record_by_id[file_id].get("sha256") != sha256:
            raise ValueError(f"duplicate row SHA-256 mismatch for File Instance: {file_id}")
        groups[group_id].append(row)

    mapping: dict[str, DuplicateInfo] = {}
    for group_id, members in sorted(groups.items()):
        group_sizes = {member.get("group_size") for member in members}
        if len(group_sizes) != 1 or next(iter(group_sizes)) != len(members):
            raise ValueError(f"duplicate group size mismatch: {group_id}")
        representatives = [
            member for member in members if member.get("is_representative") is True
        ]
        if len(representatives) != 1:
            raise ValueError(f"duplicate group must have one representative: {group_id}")
        representative_id = representatives[0]["file_instance_id"]
        sha256 = str(members[0]["sha256"])
        for member in members:
            file_id = str(member["file_instance_id"])
            if file_id in mapping:
                raise ValueError(f"File Instance appears in multiple duplicate groups: {file_id}")
            mapping[file_id] = DuplicateInfo(
                duplicate_group_id=group_id,
                sha256=sha256,
                representative_file_instance_id=representative_id,
                is_representative=file_id == representative_id,
            )
    return mapping


def _is_positive_healthy(record: Mapping[str, Any]) -> bool:
    page_count = record.get("page_count")
    return (
        record.get("inventory_status") == "success"
        and record.get("pdf_open_status") == "success"
        and isinstance(page_count, int)
        and not isinstance(page_count, bool)
        and page_count > 0
    )


def is_main_eligible(record: Mapping[str, Any]) -> bool:
    """Return the frozen Main Sample eligibility predicate."""

    return _is_positive_healthy(record) and record.get("text_layer_status") in {
        "text_present",
        "mixed_or_uncertain",
    }


def _is_duplicate_representative(
    record: Mapping[str, Any], duplicate_mapping: Mapping[str, DuplicateInfo]
) -> bool:
    info = duplicate_mapping.get(_file_id(record))
    return info is None or info.is_representative


def _collapse_exact_duplicates(
    records: Iterable[Mapping[str, Any]],
    duplicate_mapping: Mapping[str, DuplicateInfo],
) -> list[dict[str, Any]]:
    return [
        dict(record)
        for record in records
        if _is_duplicate_representative(record, duplicate_mapping)
    ]


def _make_item(
    record: Mapping[str, Any],
    *,
    pool_name: str,
    group_population: int,
    group_quota: int,
    selection_rank_or_index: int,
    sampling_method: str,
    duplicate_mapping: Mapping[str, DuplicateInfo],
) -> SampleItem:
    info = duplicate_mapping.get(_file_id(record))
    return SampleItem(
        record=dict(record),
        sample_role="main" if pool_name == "main" else "audit",
        pool_name=pool_name,
        pool_priority=POOL_PRIORITY[pool_name],
        group_population=group_population,
        group_quota=group_quota,
        selection_rank_or_index=selection_rank_or_index,
        sampling_method=sampling_method,
        duplicate_group_id=info.duplicate_group_id if info else None,
        exact_duplicate_representative=True if info is None else info.is_representative,
    )


def _select_grouped(
    candidates_by_group: Mapping[str, list[dict[str, Any]]],
    *,
    pool_name: str,
    target: int,
    duplicate_mapping: Mapping[str, DuplicateInfo],
    base_quota_per_group: int | None = None,
    sampling_method: str,
) -> tuple[tuple[SampleItem, ...], tuple[GroupQuota, ...], int]:
    """Allocate quotas and select sorted, evenly-spaced records per group."""

    normalized = {
        group: sorted(records, key=_record_sort_key)
        for group, records in sorted(candidates_by_group.items())
        if records
    }
    candidate_count = sum(len(records) for records in normalized.values())
    actual_target = min(target, candidate_count)
    if actual_target == 0:
        return (), (), candidate_count

    if base_quota_per_group is None:
        base_by_group = {
            group: min(1, len(records)) for group, records in normalized.items()
        }
    else:
        base_by_group = {
            group: min(base_quota_per_group, len(records))
            for group, records in normalized.items()
        }

    base_total = sum(base_by_group.values())
    if actual_target < base_total:
        raise ValueError(
            f"{pool_name} target {actual_target} is smaller than its required base quota {base_total}"
        )

    capacities = {
        group: len(normalized[group]) - base_by_group[group]
        for group in normalized
    }
    extra_target = actual_target - base_total
    extra_allocation, extra_floors, remainders = hamilton_allocate(
        capacities,
        extra_target,
    )

    quotas: list[GroupQuota] = []
    items: list[SampleItem] = []
    for group in sorted(normalized):
        final_quota = base_by_group[group] + extra_allocation[group]
        candidates = normalized[group]
        indexes = evenly_spaced_indices(len(candidates), final_quota)
        quotas.append(
            GroupQuota(
                pool_name=pool_name,
                parent_group=group,
                population=len(candidates),
                base_quota=base_by_group[group],
                proportional_quota=extra_floors[group],
                remainder=remainders[group],
                largest_remainder_award=extra_allocation[group] - extra_floors[group],
                final_quota=final_quota,
                actual_selected_count=len(indexes),
            )
        )
        items.extend(
            _make_item(
                candidates[index],
                pool_name=pool_name,
                group_population=len(candidates),
                group_quota=final_quota,
                selection_rank_or_index=index,
                sampling_method=sampling_method,
                duplicate_mapping=duplicate_mapping,
            )
            for index in indexes
        )
    return tuple(items), tuple(quotas), candidate_count


def _select_exception_pool(
    candidates: list[dict[str, Any]],
    *,
    target: int,
    duplicate_mapping: Mapping[str, DuplicateInfo],
) -> PoolSelection:
    ordered = sorted(candidates, key=lambda record: (_group(record), *_record_sort_key(record)))
    if target < len(ordered):
        ordered = ordered[:target]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in ordered:
        groups[_group(record)].append(record)
    quotas = tuple(
        GroupQuota(
            pool_name="source_quality_exception",
            parent_group=group,
            population=len(group_records),
            base_quota=len(group_records),
            proportional_quota=0,
            remainder=Fraction(0, 1),
            largest_remainder_award=0,
            final_quota=len(group_records),
            actual_selected_count=len(group_records),
        )
        for group, group_records in sorted(groups.items())
    )
    items = tuple(
        _make_item(
            record,
            pool_name="source_quality_exception",
            group_population=len(groups[_group(record)]),
            group_quota=len(groups[_group(record)]),
            selection_rank_or_index=index,
            sampling_method=EXCEPTION_SAMPLING_METHOD,
            duplicate_mapping=duplicate_mapping,
        )
        for index, record in enumerate(ordered)
    )
    return PoolSelection(
        pool_name="source_quality_exception",
        target=target,
        actual_count=len(items),
        candidate_count=len(candidates),
        group_quotas=quotas,
        items=items,
    )


def _group_records(records: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[_group(record)].append(dict(record))
    return dict(groups)


def _audit_candidates(
    records: Iterable[Mapping[str, Any]],
    pool_name: str,
) -> list[dict[str, Any]]:
    if pool_name == "text_absent":
        return [
            dict(record)
            for record in records
            if _is_positive_healthy(record) and record.get("text_layer_status") == "text_absent"
        ]
    if pool_name == "mixed_text":
        return [
            dict(record)
            for record in records
            if _is_positive_healthy(record)
            and record.get("text_layer_status") == "mixed_or_uncertain"
        ]
    if pool_name == "filename_unmatched":
        return [
            dict(record)
            for record in records
            if _is_positive_healthy(record)
            and record.get("filename_parse_status") == "unmatched"
        ]
    raise ValueError(f"unsupported audit pool: {pool_name}")


def build_calibration_selection(
    records: Iterable[Mapping[str, Any]],
    duplicate_rows: Iterable[Mapping[str, Any]],
    *,
    main_target: int = 600,
    base_quota_per_parent_group: int = 15,
    audit_targets: Mapping[str, int | str] | None = None,
    calibration_sample_id: str = "calibration-sample-test",
) -> CalibrationSelection:
    """Build the complete deterministic Main Sample and Audit Pool bundle."""

    if main_target < 1:
        raise ValueError("main_target must be positive")
    if base_quota_per_parent_group < 1:
        raise ValueError("base_quota_per_parent_group must be positive")
    materialized_records = [dict(record) for record in records]
    ids = [_file_id(record) for record in materialized_records]
    if len(ids) != len(set(ids)):
        raise ValueError("inventory contains duplicate File Instance IDs")
    duplicate_mapping = build_duplicate_mapping(materialized_records, duplicate_rows)
    targets: dict[str, int | str] = {
        "source_quality_exception": "all",
        "text_absent": 60,
        "mixed_text": 40,
        "filename_unmatched": 60,
    }
    if audit_targets is not None:
        targets.update(audit_targets)

    main_physical = [record for record in materialized_records if is_main_eligible(record)]
    main_collapsed = _collapse_exact_duplicates(main_physical, duplicate_mapping)
    main_items, main_quotas, _ = _select_grouped(
        _group_records(main_collapsed),
        pool_name="main",
        target=main_target,
        duplicate_mapping=duplicate_mapping,
        base_quota_per_group=base_quota_per_parent_group,
        sampling_method=MAIN_SAMPLING_METHOD,
    )
    pools: list[PoolSelection] = [
        PoolSelection(
            pool_name="main",
            target=main_target,
            actual_count=len(main_items),
            candidate_count=len(main_collapsed),
            group_quotas=main_quotas,
            items=main_items,
        )
    ]
    used_ids = {_file_id(item.record) for item in main_items}

    exception_candidates = [
        record
        for record in materialized_records
        if record.get("inventory_status") == "partial" and _file_id(record) not in used_ids
    ]
    exception_target = targets["source_quality_exception"]
    if exception_target == "all":
        exception_target_value = len(exception_candidates)
    elif isinstance(exception_target, int) and exception_target > 0:
        exception_target_value = min(exception_target, len(exception_candidates))
    else:
        raise ValueError("source_quality_exception target must be 'all' or a positive integer")
    exception_pool = _select_exception_pool(
        exception_candidates,
        target=exception_target_value,
        duplicate_mapping=duplicate_mapping,
    )
    pools.append(exception_pool)
    used_ids.update(_file_id(item.record) for item in exception_pool.items)

    for pool_name in ("text_absent", "mixed_text", "filename_unmatched"):
        candidates = [
            record
            for record in _audit_candidates(materialized_records, pool_name)
            if _file_id(record) not in used_ids
        ]
        candidates = _collapse_exact_duplicates(candidates, duplicate_mapping)
        target = targets[pool_name]
        if not isinstance(target, int) or isinstance(target, bool) or target < 1:
            raise ValueError(f"{pool_name} target must be a positive integer")
        items, quotas, candidate_count = _select_grouped(
            _group_records(candidates),
            pool_name=pool_name,
            target=target,
            duplicate_mapping=duplicate_mapping,
            base_quota_per_group=None,
            sampling_method=AUDIT_SAMPLING_METHODS[pool_name],
        )
        pool = PoolSelection(
            pool_name=pool_name,
            target=target,
            actual_count=len(items),
            candidate_count=candidate_count,
            group_quotas=quotas,
            items=items,
        )
        pools.append(pool)
        used_ids.update(_file_id(item.record) for item in items)

    main_ids = {_file_id(item.record) for item in main_items}
    audit_sets = [
        {_file_id(item.record) for item in pool.items}
        for pool in pools[1:]
    ]
    audit_union = set().union(*audit_sets) if audit_sets else set()
    audit_total = sum(len(item_ids) for item_ids in audit_sets)
    cross_pool_overlap_count = audit_total - len(audit_union)
    main_audit_overlap_count = len(main_ids & audit_union)
    if main_audit_overlap_count or cross_pool_overlap_count:
        raise ValueError("Main Sample and Audit Pools must be physically disjoint")

    all_items = tuple(
        item
        for pool in pools
        for item in sorted(
            pool.items,
            key=lambda item: (
                item.pool_priority,
                _group(item.record),
                *_record_sort_key(item.record),
            ),
        )
    )
    all_ids = [_file_id(item.record) for item in all_items]
    if len(all_ids) != len(set(all_ids)):
        raise AssertionError("selected File Instances are not globally unique")
    return CalibrationSelection(
        items=all_items,
        main_physical_eligible_count=len(main_physical),
        main_duplicate_collapsed_eligible_count=len(main_collapsed),
        exact_duplicates_excluded_from_sampling=len(main_physical) - len(main_collapsed),
        pools=tuple(pools),
        main_audit_overlap_count=main_audit_overlap_count,
        cross_pool_overlap_count=cross_pool_overlap_count,
    )


def sample_rows(
    selection: CalibrationSelection,
    *,
    phase2_run_id: str,
    calibration_sample_id: str,
    full_inventory_run_id: str,
    inventory_schema_version: str,
) -> list[dict[str, Any]]:
    """Convert selected items to the explicit calibration_sample schema rows."""

    rows: list[dict[str, Any]] = []
    for item in selection.items:
        record = item.record
        file_id = _file_id(record)
        rows.append(
            {
                "phase2_run_id": phase2_run_id,
                "calibration_sample_id": calibration_sample_id,
                "calibration_item_id": calibration_item_id(calibration_sample_id, file_id),
                "sample_role": item.sample_role,
                "pool_name": item.pool_name,
                "file_instance_id": file_id,
                "sha256": record.get("sha256"),
                "source_root_id": record.get("source_root_id"),
                "relative_path": record.get("relative_path"),
                "parent_group": record.get("parent_group"),
                "file_name": record.get("file_name"),
                "size_bytes": record.get("size_bytes"),
                "mtime_ns": record.get("mtime_ns"),
                "inventory_status": record.get("inventory_status"),
                "pdf_open_status": record.get("pdf_open_status"),
                "pdf_status": record.get("pdf_status"),
                "page_count": record.get("page_count"),
                "text_layer_status": record.get("text_layer_status"),
                "filename_parse_status": record.get("filename_parse_status"),
                "exact_duplicate_group_id": item.duplicate_group_id,
                "exact_duplicate_representative": item.exact_duplicate_representative,
                "group_population": item.group_population,
                "group_quota": item.group_quota,
                "selection_rank_or_index": item.selection_rank_or_index,
                "sampling_method": item.sampling_method,
                "full_inventory_run_id": full_inventory_run_id,
                "inventory_schema_version": inventory_schema_version,
            }
        )
    return rows


def canonical_selection_payload(selection: CalibrationSelection) -> list[dict[str, Any]]:
    """Return the stable payload used for recomputation and sample hashing."""

    return [
        {
            "pool_name": item.pool_name,
            "pool_priority": item.pool_priority,
            "parent_group": _group(item.record),
            "relative_path": item.record.get("relative_path"),
            "file_instance_id": _file_id(item.record),
            "group_population": item.group_population,
            "group_quota": item.group_quota,
            "selection_rank_or_index": item.selection_rank_or_index,
            "sampling_method": item.sampling_method,
        }
        for item in selection.items
    ]


def canonical_selection_bytes(selection: CalibrationSelection) -> bytes:
    return (
        json.dumps(
            canonical_selection_payload(selection),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
