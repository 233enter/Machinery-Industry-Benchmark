from __future__ import annotations

from pathlib import Path

from migb.inventory.identity import file_instance_id
from migb.phase2.sampling import (
    build_calibration_selection,
    calibration_item_id,
    canonical_selection_bytes,
)


def _record(
    group: str,
    relative_path: str,
    *,
    text_layer_status: str = "text_present",
    inventory_status: str = "success",
    pdf_open_status: str = "success",
    page_count: int | None = 5,
    filename_parse_status: str = "matched",
    sha256: str | None = None,
) -> dict[str, object]:
    return {
        "file_instance_id": file_instance_id("root", relative_path),
        "source_root_id": "root",
        "relative_path": relative_path,
        "file_name": Path(relative_path).name,
        "parent_group": group,
        "sha256": sha256 or f"hash-{relative_path}",
        "size_bytes": 100,
        "mtime_ns": 200,
        "inventory_status": inventory_status,
        "pdf_open_status": pdf_open_status,
        "pdf_status": "valid" if pdf_open_status == "success" else "unknown",
        "page_count": page_count,
        "text_layer_status": text_layer_status,
        "filename_parse_status": filename_parse_status,
    }


def _duplicate_rows(*members: tuple[str, str, bool]) -> list[dict[str, object]]:
    rows = []
    sha = "same-sha"
    for group_id, relative_path, representative in members:
        rows.append(
            {
                "duplicate_group_id": group_id,
                "sha256": sha,
                "group_size": len(members),
                "file_instance_id": file_instance_id("root", relative_path),
                "is_representative": representative,
            }
        )
    return rows


def test_main_eligibility_and_duplicate_collapsed_population() -> None:
    records = [
        _record("a", "a/01.pdf", sha256="same-sha"),
        _record("a", "a/02.pdf", sha256="same-sha"),
        _record("a", "a/03.pdf", text_layer_status="text_absent"),
        _record("b", "b/01.pdf", inventory_status="partial"),
        _record("b", "b/02.pdf", page_count=0),
        _record("b", "b/03.pdf", text_layer_status="mixed_or_uncertain"),
    ]
    selection = build_calibration_selection(
        records,
        _duplicate_rows(
            ("exact-same", "a/01.pdf", True),
            ("exact-same", "a/02.pdf", False),
        ),
        main_target=2,
        base_quota_per_parent_group=1,
        audit_targets={
            "source_quality_exception": "all",
            "text_absent": 1,
            "mixed_text": 1,
            "filename_unmatched": 1,
        },
    )

    assert selection.main_physical_eligible_count == 3
    assert selection.main_duplicate_collapsed_eligible_count == 2
    assert selection.exact_duplicates_excluded_from_sampling == 1
    main = selection.pools[0]
    assert main.actual_count == 2
    assert {item.record["relative_path"] for item in main.items} == {"a/01.pdf", "b/03.pdf"}


def test_main_quota_uses_hamilton_and_sorted_tie_break() -> None:
    records = [
        _record("b", f"b/{index:02d}.pdf") for index in range(5)
    ] + [
        _record("a", f"a/{index:02d}.pdf") for index in range(5)
    ]
    selection = build_calibration_selection(
        records,
        [],
        main_target=7,
        base_quota_per_parent_group=1,
        audit_targets={
            "source_quality_exception": "all",
            "text_absent": 1,
            "mixed_text": 1,
            "filename_unmatched": 1,
        },
    )
    quotas = {quota.parent_group: quota for quota in selection.pools[0].group_quotas}
    assert quotas["a"].final_quota == 4
    assert quotas["b"].final_quota == 3
    assert quotas["a"].largest_remainder_award == 1


def test_main_selection_is_evenly_spaced_and_not_first_n() -> None:
    records = [_record("a", f"a/{index:02d}.pdf") for index in range(10)]
    selection = build_calibration_selection(
        records,
        [],
        main_target=4,
        base_quota_per_parent_group=4,
        audit_targets={
            "source_quality_exception": "all",
            "text_absent": 1,
            "mixed_text": 1,
            "filename_unmatched": 1,
        },
    )
    paths = [item.record["relative_path"] for item in selection.pools[0].items]
    assert paths == ["a/00.pdf", "a/03.pdf", "a/06.pdf", "a/09.pdf"]


def test_audit_pool_priority_and_global_disjointness() -> None:
    records = [
        _record("main", "main/00-mixed.pdf", text_layer_status="mixed_or_uncertain"),
        _record(
            "text",
            "text/unmatched.pdf",
            text_layer_status="text_absent",
            filename_parse_status="unmatched",
        ),
        _record(
            "main",
            "main/10-mixed-unmatched.pdf",
            text_layer_status="mixed_or_uncertain",
            filename_parse_status="unmatched",
        ),
        _record("main", "main/20-unmatched.pdf", filename_parse_status="unmatched"),
    ]
    selection = build_calibration_selection(
        records,
        [],
        main_target=1,
        base_quota_per_parent_group=1,
        audit_targets={
            "source_quality_exception": "all",
            "text_absent": 1,
            "mixed_text": 1,
            "filename_unmatched": 1,
        },
    )
    assert [pool.pool_name for pool in selection.pools] == [
        "main",
        "source_quality_exception",
        "text_absent",
        "mixed_text",
        "filename_unmatched",
    ]
    assert [pool.actual_count for pool in selection.pools] == [1, 0, 1, 1, 1]
    assert selection.main_audit_overlap_count == 0
    assert selection.cross_pool_overlap_count == 0
    all_ids = [item.record["file_instance_id"] for item in selection.items]
    assert len(all_ids) == len(set(all_ids))


def test_audit_pool_takes_all_when_population_is_small() -> None:
    records = [
        _record("a", "a/text.pdf", text_layer_status="text_absent"),
        _record("b", "b/text.pdf", text_layer_status="text_absent"),
    ]
    selection = build_calibration_selection(
        records,
        [],
        main_target=1,
        base_quota_per_parent_group=1,
        audit_targets={
            "source_quality_exception": "all",
            "text_absent": 60,
            "mixed_text": 40,
            "filename_unmatched": 60,
        },
    )
    assert selection.pools[2].target == 60
    assert selection.pools[2].actual_count == 2


def test_calibration_identity_and_recomputation_payload_are_stable() -> None:
    records = [_record("a", "a/one.pdf")]
    first = build_calibration_selection(records, [], main_target=1)
    second = build_calibration_selection(records, [], main_target=1)
    assert canonical_selection_bytes(first) == canonical_selection_bytes(second)
    item_id = records[0]["file_instance_id"]
    assert calibration_item_id("sample", item_id) == calibration_item_id("sample", item_id)
