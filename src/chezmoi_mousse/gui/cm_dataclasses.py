from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangedPaths:
    added_managed: list[Path] = field(default_factory=lambda: [])
    changed_status: dict[Path, tuple[str, str]] = field(default_factory=lambda: {})
    removed_managed: list[Path] = field(default_factory=lambda: [])

    @property
    def added_managed_str(self) -> str:
        return "\n".join(str(p) for p in self.added_managed)

    @property
    def changed_status_str(self) -> str:
        return "\n".join(
            f"{p}:\nold status pair: '{old}' -> new status pair: '{new}'"
            for p, (old, new) in self.changed_status.items()
        )

    @property
    def removed_managed_str(self) -> str:
        return "\n".join(str(p) for p in self.removed_managed)

    @property
    def no_changes(self) -> bool:
        return (
            not self.added_managed
            and not self.changed_status
            and not self.removed_managed
        )


@dataclass(slots=True, frozen=True)
class ResultsSnapshot:
    managed_paths: set[Path] = field(default_factory=lambda: set())
    status_paths: dict[Path, str] = field(default_factory=lambda: {})
