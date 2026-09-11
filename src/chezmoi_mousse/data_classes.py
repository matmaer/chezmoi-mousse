from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.str_enums import StatusCode as CmSc

if TYPE_CHECKING:
    from chezmoi_mousse.str_enums import PathKind

__all__ = ["ChezmoiPaths", "ManagedPaths"]


@dataclass
class ChangedPaths:
    removed_dir_parents: frozenset[Path]  # should only contain the common parents
    added_dirs: frozenset[Path]  # should contain all added directories

    removed_files: frozenset[
        Path
    ]  # should only contain files with their immediate parent not removed
    added_files: frozenset[Path]  # should all added files


@dataclass
class ManagedPaths:
    # Calculated from the chezmoi command outputs
    dirs: dict[Path, PathKind]
    files: dict[Path, PathKind]
    status_paths: frozenset[Path]

    # The delta calculated after an operation or refresh in the app
    added_dirs: frozenset[Path]
    removed_dirs: frozenset[Path]  # should only contain the common parents
    added_files: frozenset[Path]
    removed_files: frozenset[Path]

    # Derived sets for convenience and frequent lookups
    paths: frozenset[Path] = frozenset()  # ALL managed paths
    space_paths: frozenset[Path] = frozenset()  # Any path with any status
    added_paths: frozenset[Path] = frozenset()

    def __post_init__(self) -> None:
        self.paths = frozenset(self.dirs | self.files)
        self.space_paths = self.paths - self.status_paths
        self.added_paths = frozenset(self.added_dirs | self.added_files)


@dataclass
class StatusPaths:
    # Can include paths with no status, if the other column has a status.
    _status_dirs: dict[Path, str]
    _status_files: dict[Path, str]

    changed_dirs: dict[Path, CmSc]
    changed_files: dict[Path, CmSc]

    # Paths in _status_dirs and _status_files with a status other than space
    status_dirs: dict[Path, CmSc] = field(default_factory=dict[Path, CmSc])
    status_files: dict[Path, CmSc] = field(default_factory=dict[Path, CmSc])
    status_paths: set[Path] = field(default_factory=set[Path])

    # Paths in _status_dirs and _status_files with no status (space)
    no_status_files: set[Path] = field(default_factory=set[Path])
    no_status_dirs: set[Path] = field(default_factory=set[Path])

    # Dirs with no status, containing ANY nested path(s) with a status, recursive.
    n_dirs: set[Path] = field(default_factory=set[Path])
    # Dirs with no status, containing ONLY nested paths(s) without a status, recursive.
    ns_dirs: set[Path] = field(default_factory=set[Path])

    def __post_init__(self) -> None:
        for path, status in self._status_dirs.items():
            if status == CmSc.Space:
                self.no_status_dirs.add(path)
            else:
                self.status_dirs[path] = CmSc(status)

        for path, status in self._status_files.items():
            if status == CmSc.Space:
                self.no_status_files.add(path)
            else:
                self.status_files[path] = CmSc(status)

        self.status_paths = set(self.status_dirs | self.status_files)

        self.n_dirs = {
            dir_path
            for dir_path in self.no_status_dirs
            if any(
                path != dir_path and path.is_relative_to(dir_path)
                for path in self.status_paths
            )
        }

        self.ns_dirs = {
            dir_path
            for dir_path in self.no_status_dirs
            if all(
                path != dir_path and path.is_relative_to(dir_path)
                for path in self.no_status_dirs | self.no_status_files
            )
        }


@dataclass(kw_only=True)
class ChezmoiPaths:
    """
    Created after each time we re-run all managed, status and the git log command.
    Command outputs are saved in store.py and used to init the class.
    The class is initialized in the store.py variable.
    """

    managed: ManagedPaths
    apply: StatusPaths
    re_add: StatusPaths
