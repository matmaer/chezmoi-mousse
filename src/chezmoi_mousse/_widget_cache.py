"""Explicit widget cache to avoid re-creating widgets or update selectively."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from textual.widgets import DataTable, Static, TextArea

__all__ = ["WidgetCache"]


@dataclass(slots=True)
class WidgetCache:
    """Gets populated each time a new path is selected in the Tree or DirectoryTree."""

    file_diffs: dict[Path, list[Static]] = field(
        default_factory=dict[Path, list[Static]]
    )
    file_reverse_diffs: dict[Path, list[Static]] = field(
        default_factory=dict[Path, list[Static]]
    )
    file_contents: dict[Path, Static | TextArea] = field(
        default_factory=dict[Path, Static | TextArea]
    )
    git_log_tables: dict[Path, DataTable[str]] = field(
        default_factory=dict[Path, DataTable[str]]
    )  # cache for both dirs and files

    def clear(self) -> None:
        """Clear all cached widgets after live operations or theme changes."""
        self.file_contents.clear()
        self.file_diffs.clear()
        self.file_reverse_diffs.clear()
        self.git_log_tables.clear()
