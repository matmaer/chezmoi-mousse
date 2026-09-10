from __future__ import annotations

from copy import copy
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from chezmoi_mousse.str_enums import PathKind, StatusCode

__all__ = ["Changed", "ManagedPaths"]


@dataclass
class StatusPaths:
    status_dirs: dict[Path, StatusCode] = field(default_factory=dict[Path, StatusCode])
    status_files: dict[Path, StatusCode] = field(default_factory=dict[Path, StatusCode])
    space_dirs: frozenset[Path] = frozenset()
    space_files: frozenset[Path] = frozenset()

    @cached_property
    def status_paths(self) -> dict[Path, StatusCode]:
        return self.status_dirs | self.status_files

    @cached_property
    def space_paths(self) -> frozenset[Path]:
        return self.space_dirs | self.space_files

    @cached_property
    def fake_status_dirs(self) -> frozenset[Path]:
        return frozenset(self.space_dirs & self.status_dirs.keys())


@dataclass(kw_only=True)
class ManagedPaths:
    # will be accessible via store.paths
    managed_dirs: dict[Path, PathKind] = field(default_factory=dict[Path, PathKind])
    managed_files: dict[Path, PathKind] = field(default_factory=dict[Path, PathKind])
    status_dir_pairs: dict[Path, str] = field(default_factory=dict[Path, str])
    status_file_pairs: dict[Path, str] = field(default_factory=dict[Path, str])

    apply: StatusPaths = field(default_factory=StatusPaths)
    re_add: StatusPaths = field(default_factory=StatusPaths)

    def __post_init__(self) -> None:
        self.apply = self.get_status_paths(0)
        self.re_add = self.get_status_paths(1)

    @cached_property
    def double_space_dirs(self) -> dict[Path, PathKind]:
        return {
            path: kind
            for path, kind in self.managed_dirs.items()
            if path not in self.status_dir_pairs
        }

    def get_status_paths(self, column: int) -> StatusPaths:
        # Return a dict which is relevant for the apply or re-add context.
        # First we check all files with and without a status code that is not a space.
        # Then we check all directories with and without a status code
        # Lastly we replace any directory which has a space as a status, with a status
        # code being "StatusCode.N_DIR" if and only if they have nested status paths,
        # for their column, no matter how deep, no matter if those are files or
        # directories.
        #
        # For files we always keep the actual status code
        # but we separate files with or without a status (a space or no space)

        # When everything is processed, we return a StatusPaths instance. We assign this
        # instance to apply for column one, and to re_add for column two.

        status_dirs: dict[Path, StatusCode] = {
            path: StatusCode(status)
            for path, status in self.status_dir_pairs.items()
            if status[column] != " "
        }
        space_dirs: frozenset[Path] = frozenset(
            path
            for path, status in self.status_dir_pairs.items()
            if status[column] == " "
        )
        status_files: dict[Path, StatusCode] = {
            path: StatusCode(status)
            for path, status in self.status_file_pairs.items()
            if status[column] != " "
        }
        space_files: frozenset[Path] = frozenset(
            path
            for path, status in self.status_file_pairs.items()
            if status[column] == " "
        )
        n_dirs = frozenset(
            directory
            for directory in space_dirs
            if any(
                path != directory and path.is_relative_to(directory)
                for path in set(status_dirs) | set(status_files)
            )
        )

        status_dirs.update(dict.fromkeys(n_dirs, StatusCode.N_DIR))

        return StatusPaths(
            status_dirs=status_dirs,
            status_files=status_files,
            space_dirs=space_dirs,
            space_files=space_files,
        )


@dataclass(slots=True)
class Changed:
    _added_managed_dirs: set[Path] = field(default_factory=set[Path])
    _added_managed_files: set[Path] = field(default_factory=set[Path])
    _removed_managed_dirs: set[Path] = field(default_factory=set[Path])
    _removed_managed_files: set[Path] = field(default_factory=set[Path])
    _changed_status_dirs: dict[Path, tuple[str, str]] = field(
        default_factory=dict[Path, tuple[str, str]]
    )
    _changed_status_files: dict[Path, tuple[str, str]] = field(
        default_factory=dict[Path, tuple[str, str]]
    )

    _old_managed_paths: ManagedPaths | None = None

    def backup_managed_paths(self, managed_paths: ManagedPaths) -> None:
        backup = copy(managed_paths)
        backup.managed_dirs = managed_paths.managed_dirs.copy()
        backup.managed_files = managed_paths.managed_files.copy()
        backup.status_dir_pairs = managed_paths.status_dir_pairs.copy()
        backup.status_file_pairs = managed_paths.status_file_pairs.copy()
        self._old_managed_paths = backup

    def update_changed_paths(self, managed_paths: ManagedPaths) -> None:

        if self._old_managed_paths is None:
            self._old_managed_paths = ManagedPaths()

        self._added_managed_dirs = set()
        self._added_managed_files = set()
        self._removed_managed_dirs = set()
        self._removed_managed_files = set()
        self._changed_status_dirs = {}
        self._changed_status_files = {}

        old_managed = self._old_managed_paths
        self._added_managed_dirs = set(managed_paths.managed_dirs) - set(
            old_managed.managed_dirs
        )
        self._added_managed_files = set(managed_paths.managed_files) - set(
            old_managed.managed_files
        )
        self._removed_managed_dirs = set(old_managed.managed_dirs) - set(
            managed_paths.managed_dirs
        )
        self._removed_managed_files = set(old_managed.managed_files) - set(
            managed_paths.managed_files
        )

        self._changed_status_dirs = {
            path: (
                old_managed.status_dir_pairs[path],
                managed_paths.status_dir_pairs[path],
            )
            for path in old_managed.status_dir_pairs.keys()
            & managed_paths.status_dir_pairs.keys()
            if old_managed.status_dir_pairs[path]
            != managed_paths.status_dir_pairs[path]
        }
        self._changed_status_files = {
            path: (
                old_managed.status_file_pairs[path],
                managed_paths.status_file_pairs[path],
            )
            for path in old_managed.status_file_pairs.keys()
            & managed_paths.status_file_pairs.keys()
            if old_managed.status_file_pairs[path]
            != managed_paths.status_file_pairs[path]
        }

    @property
    def added_managed_dirs(self) -> set[Path]:
        return self._added_managed_dirs

    @property
    def added_managed_files(self) -> set[Path]:
        return self._added_managed_files

    @property
    def removed_managed_dirs(self) -> set[Path]:
        return self._removed_managed_dirs

    @property
    def removed_managed_files(self) -> set[Path]:
        return self._removed_managed_files

    @property
    def changed_status_dirs(self) -> dict[Path, tuple[str, str]]:
        return self._changed_status_dirs

    @property
    def changed_status_files(self) -> dict[Path, tuple[str, str]]:
        return self._changed_status_files

    @property
    def no_changed_paths(self) -> bool:
        return (
            not self._added_managed_dirs
            and not self._added_managed_files
            and not self._removed_managed_dirs
            and not self._removed_managed_files
            and not self._changed_status_dirs
            and not self._changed_status_files
        )
