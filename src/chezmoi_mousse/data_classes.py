from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from chezmoi_mousse.named_tuples import StatusPairsDict
from chezmoi_mousse.str_enums import ChezmoiStatusCode as CmSc

__all__ = ["ChezmoiPaths"]


ManagedChange = NamedTuple(
    "ManagedChange",
    added=list[Path],
    removed=list[Path],
)

StatusChange = NamedTuple(
    "StatusChange",
    path=Path,
    old_status=str,
    new_status=str,
)

Changes = NamedTuple(
    "Changes",
    managed_dirs=ManagedChange,
    managed_files=ManagedChange,
    dir_status_pairs=list[StatusChange],
    file_status_pairs=list[StatusChange],
)

ManagedPaths = NamedTuple(
    "ManagedPaths",
    all=set[Path],
    dirs=list[Path],
    files=list[Path],
    status_dirs=StatusPairsDict,
    status_files=StatusPairsDict,
    missing=set[Path],
)

StatusByColumn = NamedTuple(
    "StatusByColumn",
    all=set[Path],
    dirs=dict[Path, CmSc],
    files=dict[Path, CmSc],
    n_dirs=set[Path],
    ns_dirs=set[Path],
    space_dirs=set[Path],
    space_files=set[Path],
)


@dataclass(kw_only=True)
class ChezmoiPaths:
    """
    Created after each time we re-run all managed, status and the git log command.

    The NamedTuple classes allows typed dot-accessing attributes.

    Changes: (available via dot-accessing 'changed')
    - Fields are mutually exclusive, unchanged paths are not included.
    - Updated after refresh or operation, to report on all changed paths in the UI.

    ManagedPaths: (available via dot-accessing 'managed' attribute)

    StatusByColumn: (available via dot-accessing the 'apply' or 're_add' attribute)
    - has two instances: one for the 'apply' status and one for the 're_add' status.
    - n_dirs: dirs with no status, containing ANY nested path(s) with a status.
    - ns_dirs: dirs with no status, containing ONLY nested paths(s) without a status

    """

    _old_managed_dirs: set[Path]
    _new_managed_dirs: set[Path]

    _old_managed_files: set[Path]
    _new_managed_files: set[Path]

    _old_dir_status_pairs: StatusPairsDict
    _new_dir_status_pairs: StatusPairsDict

    _old_file_status_pairs: StatusPairsDict
    _new_file_status_pairs: StatusPairsDict

    changes = Changes(
        managed_dirs=ManagedChange(added=[], removed=[]),
        managed_files=ManagedChange(added=[], removed=[]),
        dir_status_pairs=[],
        file_status_pairs=[],
    )
    managed = ManagedPaths(
        all=set(), dirs=[], files=[], status_dirs={}, status_files={}, missing=set()
    )
    apply = StatusByColumn(
        all=set(),
        dirs={},
        files={},
        n_dirs=set(),
        ns_dirs=set(),
        space_dirs=set(),
        space_files=set(),
    )
    re_add = StatusByColumn(
        all=set(),
        dirs={},
        files={},
        n_dirs=set(),
        ns_dirs=set(),
        space_dirs=set(),
        space_files=set(),
    )

    def __post_init__(self) -> None:
        if not self._new_dir_status_pairs and not self._new_file_status_pairs:
            self.no_status_paths = True
        self._calculate_changes_attrib()
        self._calculate_managed_attrib()
        self._calculate_status_by_column(0)
        self._calculate_status_by_column(1)

    def _calculate_changes_attrib(self) -> None:
        added_dirs = sorted(self._new_managed_dirs - self._old_managed_dirs)
        added_files = sorted(self._new_managed_files - self._old_managed_files)
        removed_dirs = sorted(self._old_managed_dirs - self._new_managed_dirs)
        removed_files = sorted(self._old_managed_files - self._new_managed_files)
        self.changes = Changes(
            managed_dirs=ManagedChange(
                added=added_dirs,
                removed=removed_dirs,
            ),
            managed_files=ManagedChange(
                added=added_files,
                removed=removed_files,
            ),
            dir_status_pairs=self._new_dir_status_pairs,
            file_status_pairs=self._new_file_status_pairs,
        )

    def _calculate_managed_attrib(self) -> None:
        self.managed = ManagedPaths(
            all=self._new_managed_dirs | self._new_managed_files,
            dirs=sorted(self._new_managed_dirs),
            files=sorted(self._new_managed_files),
            status_dirs=self._new_dir_status_pairs,
            status_files=self._new_file_status_pairs,
            missing={
                p
                for p in self._new_managed_dirs | self._new_managed_files
                if not p.exists()
            },
        )

    def _calculate_status_by_column(self, column: int) -> None:

        status_dirs = {
            path: status_pair[column]
            for path, status_pair in self._new_dir_status_pairs.items()
        }
        status_files = {
            path: status_pair[column]
            for path, status_pair in self._new_file_status_pairs.items()
        }
        space_dirs: set[Path] = set()
        for path, status in status_dirs.items():
            if status == CmSc.Space:
                space_dirs.add(path)
            else:
                status_dirs[path] = CmSc(status)

        space_files: set[Path] = set()
        for path, status in status_files.items():
            if status == CmSc.Space:
                space_files.add(path)
            else:
                status_files[path] = CmSc(status)

        status_paths = set(status_dirs | status_files)

        n_dirs = {
            dir_path
            for dir_path in space_dirs
            if any(
                path != dir_path and path.is_relative_to(dir_path)
                for path in status_paths
            )
        }

        ns_dirs = {
            dir_path
            for dir_path in space_dirs
            if all(
                path != dir_path and path.is_relative_to(dir_path)
                for path in space_dirs | space_files
            )
        }

        result = StatusByColumn(
            all=status_paths,
            dirs=status_dirs,
            files=status_files,
            n_dirs=n_dirs,
            ns_dirs=ns_dirs,
            space_dirs=space_dirs,
            space_files=space_files,
        )

        if column == 1:
            self.apply = result
        else:
            self.re_add = result
