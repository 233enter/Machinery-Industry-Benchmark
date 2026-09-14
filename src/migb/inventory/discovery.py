"""NUL-safe, structured PDF discovery."""

from __future__ import annotations

import os
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DiscoveryError(RuntimeError):
    """Raised when a source root cannot be traversed safely."""


@dataclass(frozen=True)
class DiscoveredFile:
    source_root_id: str
    path: Path
    relative_path: str
    file_name: str
    parent_group: str
    extension: str


@dataclass(frozen=True)
class SourceSnapshot:
    """Structured, deterministic state captured for one discovery result."""

    entries: tuple[dict[str, Any], ...]
    source_roots: tuple[dict[str, Any], ...]
    discovered_count: int
    total_size_bytes: int
    top_level_group_count: int
    source_snapshot_fingerprint: str

    def summary(self) -> dict[str, Any]:
        return {
            "source_root_id": (
                self.source_roots[0]["source_root_id"]
                if len(self.source_roots) == 1
                else None
            ),
            "discovered_count": self.discovered_count,
            "total_size_bytes": self.total_size_bytes,
            "top_level_group_count": self.top_level_group_count,
            "source_snapshot_fingerprint": self.source_snapshot_fingerprint,
            "source_roots": [dict(root) for root in self.source_roots],
        }

    def as_dict(self) -> dict[str, Any]:
        payload = self.summary()
        payload["entries"] = [dict(entry) for entry in self.entries]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SourceSnapshot":
        entries = payload.get("entries")
        source_roots = payload.get("source_roots")
        if not isinstance(entries, list) or not isinstance(source_roots, list):
            raise ValueError("source snapshot must contain entries and source_roots lists")
        required_summary_fields = (
            "discovered_count",
            "total_size_bytes",
            "top_level_group_count",
            "source_snapshot_fingerprint",
        )
        if any(field not in payload for field in required_summary_fields):
            raise ValueError("source snapshot is missing summary fields")
        return cls(
            entries=tuple(dict(entry) for entry in entries),
            source_roots=tuple(dict(root) for root in source_roots),
            discovered_count=int(payload["discovered_count"]),
            total_size_bytes=int(payload["total_size_bytes"]),
            top_level_group_count=int(payload["top_level_group_count"]),
            source_snapshot_fingerprint=str(payload["source_snapshot_fingerprint"]),
        )


def capture_source_snapshot(discovered: list[DiscoveredFile]) -> SourceSnapshot:
    """Capture source metadata and fingerprint it using structured JSON.

    The fingerprint intentionally includes only the stable, operational input
    fields required by the Full Inventory contract.  JSON serialization keeps
    newline and other special characters in filenames unambiguous.
    """

    ordered = sorted(
        discovered,
        key=lambda item: (item.source_root_id, item.relative_path),
    )
    entries: list[dict[str, Any]] = []
    groups: dict[str, set[str]] = {}
    root_totals: dict[str, dict[str, Any]] = {}
    for item in ordered:
        try:
            stat_result = item.path.stat()
        except OSError as exc:
            raise DiscoveryError(
                f"cannot stat source file for snapshot {item.path}: {exc}"
            ) from exc
        entry = {
            "source_root_id": item.source_root_id,
            "relative_path": item.relative_path,
            "size_bytes": stat_result.st_size,
            "mtime_ns": stat_result.st_mtime_ns,
        }
        entries.append(entry)
        groups.setdefault(item.source_root_id, set()).add(item.parent_group)
        root_summary = root_totals.setdefault(
            item.source_root_id,
            {"source_root_id": item.source_root_id, "discovered_count": 0, "total_size_bytes": 0},
        )
        root_summary["discovered_count"] += 1
        root_summary["total_size_bytes"] += stat_result.st_size

    canonical = json.dumps(
        entries,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    fingerprint = hashlib.sha256(canonical).hexdigest()
    source_roots = []
    for source_root_id in sorted(root_totals):
        source_roots.append(
            {
                **root_totals[source_root_id],
                "top_level_group_count": len(groups.get(source_root_id, set())),
            }
        )
    return SourceSnapshot(
        entries=tuple(entries),
        source_roots=tuple(source_roots),
        discovered_count=len(entries),
        total_size_bytes=sum(int(entry["size_bytes"]) for entry in entries),
        top_level_group_count=sum(len(group_values) for group_values in groups.values()),
        source_snapshot_fingerprint=fingerprint,
    )


def compare_source_snapshots(
    before: SourceSnapshot,
    after: SourceSnapshot,
    *,
    example_limit: int = 20,
) -> dict[str, Any]:
    """Compare structured source snapshots without flattening paths to lines."""

    def key(entry: dict[str, Any]) -> tuple[str, str]:
        return str(entry["source_root_id"]), str(entry["relative_path"])

    before_by_key = {key(entry): entry for entry in before.entries}
    after_by_key = {key(entry): entry for entry in after.entries}
    added = sorted(set(after_by_key) - set(before_by_key))
    missing = sorted(set(before_by_key) - set(after_by_key))
    metadata_changed = sorted(
        item_key
        for item_key in set(before_by_key) & set(after_by_key)
        if (
            before_by_key[item_key].get("size_bytes")
            != after_by_key[item_key].get("size_bytes")
            or before_by_key[item_key].get("mtime_ns")
            != after_by_key[item_key].get("mtime_ns")
        )
    )

    def format_key(item_key: tuple[str, str]) -> str:
        return f"{item_key[0]}:{item_key[1]}"

    return {
        "match": before.source_snapshot_fingerprint == after.source_snapshot_fingerprint,
        "added_count": len(added),
        "missing_count": len(missing),
        "metadata_changed_count": len(metadata_changed),
        "added_examples": [format_key(item) for item in added[:example_limit]],
        "missing_examples": [format_key(item) for item in missing[:example_limit]],
        "metadata_changed_examples": [
            format_key(item) for item in metadata_changed[:example_limit]
        ],
    }


def _record(root_id: str, root: Path, path: Path) -> DiscoveredFile:
    relative = path.relative_to(root)
    relative_path = relative.as_posix()
    parts = relative.parts
    return DiscoveredFile(
        source_root_id=root_id,
        path=path,
        relative_path=relative_path,
        file_name=path.name,
        parent_group=parts[0] if len(parts) > 1 else "",
        extension=path.suffix,
    )


def discover_pdfs(source_root_id: str, root: str | Path) -> list[DiscoveredFile]:
    """Discover regular files with a case-insensitive .pdf extension."""

    root_path = Path(root)
    if not root_path.exists() or not root_path.is_dir():
        raise DiscoveryError(f"source root is not an accessible directory: {root_path}")

    discovered: list[DiscoveredFile] = []
    directories = [root_path]
    while directories:
        current = directories.pop()
        try:
            with os.scandir(current) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as exc:
            raise DiscoveryError(f"cannot traverse source directory {current}: {exc}") from exc

        child_directories: list[Path] = []
        for entry in entries:
            entry_path = Path(entry.path)
            try:
                if entry.is_dir(follow_symlinks=False):
                    child_directories.append(entry_path)
                elif entry.is_file(follow_symlinks=False) and entry.name.lower().endswith(".pdf"):
                    discovered.append(_record(source_root_id, root_path, entry_path))
            except OSError as exc:
                raise DiscoveryError(f"cannot inspect directory entry {entry_path}: {exc}") from exc
        directories.extend(reversed(child_directories))

    return discovered
