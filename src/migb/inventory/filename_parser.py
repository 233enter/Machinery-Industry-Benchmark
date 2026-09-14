"""Conservative filename metadata parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FilenameParseResult:
    filename_year: str | None
    filename_issue: str | None
    filename_title: str | None
    filename_parse_status: str


_PATTERN = re.compile(
    r"【(?P<year>\d{4})-(?P<issue>\d{2})】(?P<title>[\s\S]+)\.pdf$",
    re.IGNORECASE,
)


def parse_filename(file_name: str) -> FilenameParseResult:
    """Parse only the explicitly frozen YYYY-MM filename pattern."""

    try:
        match = _PATTERN.fullmatch(file_name)
    except (TypeError, re.error):
        return FilenameParseResult(None, None, None, "error")
    if not match:
        return FilenameParseResult(None, None, None, "unmatched")
    return FilenameParseResult(
        filename_year=match.group("year"),
        filename_issue=match.group("issue"),
        filename_title=match.group("title"),
        filename_parse_status="matched",
    )
