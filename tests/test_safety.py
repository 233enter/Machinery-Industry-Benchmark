from __future__ import annotations

from pathlib import Path

import pytest

from migb.inventory.safety import SafetyError, assert_output_path_safe


def test_output_path_is_safe_when_outside_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "derived"
    source.mkdir()

    assert assert_output_path_safe([source], output) == output.resolve()


@pytest.mark.parametrize("output_name", ["source", "source/derived"])
def test_output_path_rejects_source_equality_or_descendant(
    tmp_path: Path, output_name: str
) -> None:
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(SafetyError, match="unsafe output path overlap"):
        assert_output_path_safe([source], tmp_path / output_name)


def test_output_path_rejects_source_ancestor_and_resolved_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(SafetyError):
        assert_output_path_safe([source], tmp_path)

    source_alias = tmp_path / "source-alias"
    source_alias.symlink_to(source, target_is_directory=True)
    with pytest.raises(SafetyError):
        assert_output_path_safe([source], source_alias)
