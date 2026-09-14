from __future__ import annotations

import uuid
from pathlib import PurePosixPath

import pytest

from migb.inventory.identity import (
    canonical_file_instance_name,
    file_instance_id,
    relative_path_posix,
)


def test_file_instance_id_is_deterministic_and_uses_uuid5() -> None:
    relative_path = "机械资料/章节\n一/【2024-01】轴承.pdf"
    canonical_name = canonical_file_instance_name("cmes_journal", relative_path)

    first = file_instance_id("cmes_journal", relative_path)
    second = file_instance_id("cmes_journal", relative_path)

    assert first == second
    assert first == str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_name))
    assert "章节\n一" in canonical_name


def test_identity_preserves_unicode_and_changes_after_rename() -> None:
    original = file_instance_id("cmes_journal", PurePosixPath("中文/原文件.pdf"))
    renamed = file_instance_id("cmes_journal", PurePosixPath("中文/改名.pdf"))

    assert original != renamed
    assert relative_path_posix(PurePosixPath("中文/原文件.pdf")) == "中文/原文件.pdf"


def test_absolute_relative_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be absolute"):
        file_instance_id("cmes_journal", "/absolute/file.pdf")
