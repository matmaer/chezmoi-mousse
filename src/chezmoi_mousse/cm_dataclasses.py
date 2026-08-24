from dataclasses import dataclass, field
from pathlib import Path

from chezmoi_mousse.named_tuples import PathStatus

__all__ = ("Changed",)


@dataclass(slots=True)
class Changed:
    added_managed: list[Path] = field(default_factory=lambda: [])
    removed_managed: list[Path] = field(default_factory=lambda: [])
    changed_status: dict[Path, tuple[str, str]] = field(default_factory=lambda: {})
    changed_paths: bool = False

    _old_managed_paths: frozenset[Path] = field(default_factory=lambda: frozenset())
    _old_status_paths: dict[Path, PathStatus] = field(default_factory=lambda: {})

    def update_changed_paths(self) -> None:
        from chezmoi_mousse import store

        self.added_managed = []
        self.removed_managed = []
        self.changed_status = {}

        managed_paths = store.managed_paths
        status_paths = store.status_dirs | store.status_files
        self._old_managed_paths = managed_paths.copy()
        self._old_status_paths = status_paths.copy()

        removed_managed = self._old_managed_paths - managed_paths
        added_managed = managed_paths - self._old_managed_paths

        _changed_status = {}
        intersection = self._old_managed_paths & managed_paths

        for path in intersection:
            old_code = self._old_status_paths.get(path, "  ")
            new_code = status_paths.get(path, "  ")

            if old_code != new_code:
                _changed_status[path] = (old_code, new_code)

        self.added_managed = sorted(added_managed)
        self.changed_status = _changed_status
        self.removed_managed = sorted(removed_managed)

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
    def no_changed_paths(self) -> bool:
        return (
            not self.added_managed
            and not self.changed_status
            and not self.removed_managed
        )
