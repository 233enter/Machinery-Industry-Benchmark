"""Stable CorpusFileInstance identity helpers."""

from __future__ import annotations

import uuid
from pathlib import PurePath


def relative_path_posix(relative_path: str | PurePath) -> str:
    """Return a relative path in POSIX representation without content normalization."""

    if isinstance(relative_path, PurePath):
        if relative_path.is_absolute():
            raise ValueError("relative_path must not be absolute")
        value = relative_path.as_posix()
    else:
        value = str(relative_path)
        if value.startswith("/"):
            raise ValueError("relative_path must not be absolute")
    if not value:
        raise ValueError("relative_path must not be empty")
    return value


def canonical_file_instance_name(source_root_id: str, relative_path: str | PurePath) -> str:
    """Build the v0.1 UUIDv5 canonical name."""

    if not source_root_id:
        raise ValueError("source_root_id must not be empty")
    return f"migb://file-instance/{source_root_id}/{relative_path_posix(relative_path)}"


def file_instance_id(source_root_id: str, relative_path: str | PurePath) -> str:
    """Return deterministic UUIDv5 identity for a file instance."""

    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_file_instance_name(source_root_id, relative_path)))
