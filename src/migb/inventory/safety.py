"""Source/output path safety checks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


class SafetyError(RuntimeError):
    """Raised when a source and output path overlap."""


def _is_same_or_child(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def assert_output_path_safe(source_roots: Iterable[str | Path], output_root: str | Path) -> Path:
    """Reject equality or ancestor/descendant overlap before output creation."""

    output = Path(output_root).expanduser().resolve(strict=False)
    canonical_sources = [Path(root).expanduser().resolve(strict=False) for root in source_roots]
    for source in canonical_sources:
        if _is_same_or_child(output, source) or _is_same_or_child(source, output):
            raise SafetyError(
                f"unsafe output path overlap: source={source} output={output}; "
                "output must be outside every configured source root"
            )
    return output
