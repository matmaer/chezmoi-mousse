from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import StatusCode

__all__ = ["Changed", "ChezmoiRepoChecks", "StatusPaths"]


@dataclass(slots=True)
class ChezmoiRepoChecks:
    exists_bool: bool | None = None
    has_commits_bool: bool | None = None
    has_managed_paths_bool: bool | None = None
    has_status_paths_bool: bool | None = None

    @property
    def exists(self) -> bool:
        if self.exists_bool is None:
            raise RuntimeError("Accessing exists before it is set")
        return self.exists_bool

    @property
    def has_commits(self) -> bool:
        if self.has_commits_bool is None:
            raise RuntimeError("Accessing has_commits before it is set")
        return self.has_commits_bool

    @property
    def has_managed_paths(self) -> bool:
        if self.has_managed_paths_bool is None:
            raise RuntimeError("Accessing has_managed_paths before it is set")
        return self.has_managed_paths_bool

    @property
    def has_status_paths(self) -> bool:
        if self.has_status_paths_bool is None:
            raise RuntimeError("Accessing has_status_paths before it is set")
        return self.has_status_paths_bool


@dataclass(slots=True, kw_only=True)
class StatusPaths:
    # will be accessible via store.paths
    dirs: dict[Path, StatusCode]
    files: dict[Path, StatusCode]
    space_dirs: frozenset[Path] = frozenset()
    space_files: frozenset[Path] = frozenset()
    n_dirs: frozenset[Path] = frozenset()
    tree_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        self.space_dirs = frozenset(
            path for path in store.managed_dirs if path not in self.dirs
        )
        self.space_files = frozenset(
            path for path in store.managed_files if path not in self.files
        )
        self.n_dirs = self._get_n_dirs()
        self._set_n_dir_status()

    def _get_n_dirs(self) -> frozenset[Path]:
        return frozenset(
            parent
            for path in store.managed_dirs | self.files
            for parent in path.parents
            if parent not in self.dirs
            and parent.is_relative_to(store.cfg.dest_dir)
            and parent != store.cfg.dest_dir
        )

    def _set_n_dir_status(self) -> None:
        for path, status in self.dirs.items():
            if path in self.n_dirs and status not in (
                StatusCode.Space,
                StatusCode.N_DIR,
            ):
                self.tree_dirs[path] = StatusCode.N_DIR


@dataclass(slots=True)
class Changed:
    added_managed: list[Path] = field(default_factory=lambda: [])
    removed_managed: list[Path] = field(default_factory=lambda: [])
    changed_status: dict[Path, tuple[str, str]] = field(default_factory=lambda: {})
    changed_paths: bool = False

    _old_managed_paths: set[Path] = field(default_factory=lambda: set())
    _old_status_paths: dict[Path, str] = field(default_factory=lambda: {})

    def update_changed_paths(self) -> None:
        from chezmoi_mousse import store

        self.added_managed = []
        self.removed_managed = []
        self.changed_status = {}

        managed_paths = set(store.managed_dirs | store.managed_files)
        status_paths = store.status_dirs_kind | store.status_files_kind
        self._old_managed_paths = managed_paths.copy()
        self._old_status_paths = store.dir_status_pairs | store.file_status_pairs

        removed_managed = self._old_managed_paths - managed_paths
        added_managed = managed_paths - self._old_managed_paths

        _changed_status = {}
        intersection = self._old_managed_paths & managed_paths

        for path in intersection:
            old_code = status_paths.get(path, "  ")
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
