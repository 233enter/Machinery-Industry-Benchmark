"""Explicit PyArrow schemas for D1 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq


INVENTORY_SCHEMA_VERSION = "d1-v0.1"


def _string(name: str) -> pa.Field:
    return pa.field(name, pa.string(), nullable=True)


def _integer(name: str) -> pa.Field:
    return pa.field(name, pa.int64(), nullable=True)


def _boolean(name: str) -> pa.Field:
    return pa.field(name, pa.bool_(), nullable=True)


def files_schema() -> pa.Schema:
    fields = [
        _string("inventory_schema_version"),
        _string("file_instance_id"),
        _string("source_root_id"),
        _string("relative_path"),
        _string("file_name"),
        _string("parent_group"),
        _string("extension"),
        _integer("size_bytes"),
        _integer("mtime_ns"),
        _boolean("source_changed_during_run"),
        _string("sha256"),
        _string("hash_status"),
        _string("pdf_open_status"),
        _string("pdf_error_category"),
        _string("pdf_status"),
        _boolean("is_encrypted"),
        _string("pdf_version"),
        _integer("page_count"),
        _string("metadata_title"),
        _string("metadata_author"),
        _string("metadata_subject"),
        _string("metadata_keywords"),
        _string("metadata_creator"),
        _string("metadata_producer"),
        _string("metadata_creation_date"),
        _string("metadata_modification_date"),
        _integer("sampled_page_count"),
        _integer("sampled_text_char_count"),
        _string("text_layer_status"),
        _string("filename_year"),
        _string("filename_issue"),
        _string("filename_title"),
        _string("filename_parse_status"),
        _string("inventory_status"),
        _string("collected_at"),
        _string("inventory_run_id"),
    ]
    return pa.schema(fields)


def duplicate_groups_schema() -> pa.Schema:
    return pa.schema(
        [
            _string("duplicate_group_id"),
            _string("sha256"),
            _integer("group_size"),
            _string("file_instance_id"),
            _boolean("is_representative"),
        ]
    )


def errors_schema() -> pa.Schema:
    return pa.schema(
        [
            _string("inventory_run_id"),
            _string("file_instance_id"),
            _string("source_root_id"),
            _string("relative_path"),
            _string("stage"),
            _string("error_category"),
            _string("error_message"),
            _string("timestamp"),
        ]
    )


def write_parquet(rows: Iterable[dict[str, Any]], path: str | Path, schema: pa.Schema) -> None:
    """Write rows using an explicit schema, including valid zero-row artifacts."""

    output = Path(path)
    table = pa.Table.from_pylist(list(rows), schema=schema)
    pq.write_table(table, output)
