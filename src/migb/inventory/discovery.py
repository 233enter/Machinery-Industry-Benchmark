"""NUL-safe, structured PDF discovery."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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
