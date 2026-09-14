from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from migb.inventory.artifacts import group_exact_duplicates
from migb.inventory.schema import (
    duplicate_groups_schema,
    errors_schema,
    files_schema,
    write_parquet,
)


def test_exact_duplicate_group_has_one_row_per_member() -> None:
    records = [
        {
            "file_instance_id": "id-b",
            "source_root_id": "root",
            "relative_path": "b.pdf",
            "sha256": "same-hash",
            "hash_status": "success",
        },
        {
            "file_instance_id": "id-a",
            "source_root_id": "root",
            "relative_path": "a.pdf",
            "sha256": "same-hash",
            "hash_status": "success",
        },
        {
            "file_instance_id": "id-unique",
            "source_root_id": "root",
            "relative_path": "unique.pdf",
            "sha256": "unique-hash",
            "hash_status": "success",
        },
        {
            "file_instance_id": "id-failed",
            "source_root_id": "root",
            "relative_path": "failed.pdf",
            "sha256": "same-hash",
            "hash_status": "failed",
        },
    ]

    rows = group_exact_duplicates(records)

    assert len(rows) == 2
    assert {row["file_instance_id"] for row in rows} == {"id-a", "id-b"}
    assert all(row["group_size"] == 2 for row in rows)
    assert next(row for row in rows if row["file_instance_id"] == "id-a")[
        "is_representative"
    ] is True
    assert next(row for row in rows if row["file_instance_id"] == "id-b")[
        "is_representative"
    ] is False


def test_zero_row_parquet_artifacts_keep_explicit_schema(tmp_path: Path) -> None:
    cases = [
        ("files.parquet", files_schema()),
        ("duplicate_groups.parquet", duplicate_groups_schema()),
        ("errors.parquet", errors_schema()),
    ]

    for filename, schema in cases:
        path = tmp_path / filename
        write_parquet([], path, schema)
        table = pq.read_table(path)

        assert table.num_rows == 0
        assert table.schema.equals(schema)
