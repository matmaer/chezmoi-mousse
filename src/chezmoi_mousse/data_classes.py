from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from chezmoi_mousse.str_enums import ChezmoiStatusCode as CmSc

__all__ = ["ChezmoiPaths", "StatusByColumn"]


StatusChange = NamedTuple(
    "StatusChange",
    old_status=str,
    new_status=str,
)

ManagedChange = NamedTuple(
    "ManagedChange",
    added=list[Path],
    removed=list[Path],
)

Changes = NamedTuple(
    "Changes",
    managed_dirs=ManagedChange,
    managed_files=ManagedChange,
    status_dirs=dict[Path, StatusChange],
    status_files=dict[Path, StatusChange],
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


class ChezmoiPaths:
    """Created after each time we re-run all managed, status, and git log commands."""

    changes: Changes
    apply: StatusByColumn
    re_add: StatusByColumn

    def __init__(
        self,
        *,
        managed_dirs: list[Path],
        managed_files: list[Path],
        old_man_dirs_set: set[Path],
        old_man_files_set: set[Path],
        status_dirs: dict[Path, str],
        status_files: dict[Path, str],
        old_status_dirs: dict[Path, str],
        old_status_files: dict[Path, str],
    ) -> None:

        self.managed_dirs = managed_dirs
        self.managed_files = managed_files
        self.status_dirs = status_dirs
        self.status_files = status_files

        self.managed_paths = set(managed_dirs + managed_files)
        self.status_paths = set(status_dirs | status_files)
        self.missing_paths: set[Path] = {
            p for p in self.managed_paths if not p.exists()
        }

        self.changes = self._calculate_managed_changes(
            old_man_dirs_set,
            old_man_files_set,
            old_status_dirs,
            old_status_files,
        )
        self.re_add = self._calculate_status_by_column(0, status_dirs, status_files)
        self.apply = self._calculate_status_by_column(1, status_dirs, status_files)

    def _calculate_managed_changes(
        self,
        old_man_dirs_set: set[Path],
        old_man_files_set: set[Path],
        old_status_dirs: dict[Path, str],
        old_status_files: dict[Path, str],
    ) -> Changes:

        current_dirs_set = set(self.managed_dirs)
        current_files_set = set(self.managed_files)

        def create_changed_dict(
            old_dict: dict[Path, str],
            current_dict: dict[Path, str],
        ) -> dict[Path, StatusChange]:
            return {
                k: StatusChange(old_status=old_dict[k], new_status=current_dict[k])
                for k in old_dict.keys() & current_dict.keys()
                if old_dict[k] != current_dict[k]
            }

        # Remove items from dict no longer in self.managed_paths
        old_status_dirs_pruned = {
            k: v for k, v in old_status_dirs.items() if k in self.managed_paths
        }
        old_status_files_pruned = {
            k: v for k, v in old_status_files.items() if k in self.managed_paths
        }

        return Changes(
            managed_dirs=ManagedChange(
                added=sorted(current_dirs_set - old_man_dirs_set),
                removed=sorted(old_man_dirs_set - current_dirs_set),
            ),
            managed_files=ManagedChange(
                added=sorted(current_files_set - old_man_files_set),
                removed=sorted(old_man_files_set - current_files_set),
            ),
            # Create dict[Path, StatusChange] for status_dirs and status_files
            status_dirs=create_changed_dict(old_status_dirs_pruned, self.status_dirs),
            status_files=create_changed_dict(
                old_status_files_pruned, self.status_files
            ),
        )

    def _calculate_status_by_column(
        self,
        column: int,
        dir_status_pairs: dict[Path, str],
        file_status_pairs: dict[Path, str],
    ) -> StatusByColumn:
        status_dirs = {
            path: status_pair[column] for path, status_pair in dir_status_pairs.items()
        }
        status_files = {
            path: status_pair[column] for path, status_pair in file_status_pairs.items()
        }

        space_dirs = {
            path for path, status in status_dirs.items() if status == CmSc.Space
        }
        space_files = {
            path for path, status in status_files.items() if status == CmSc.Space
        }

        for path, status in status_dirs.items():
            if status != CmSc.Space:
                status_dirs[path] = CmSc(status)

        for path, status in status_files.items():
            if status != CmSc.Space:
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

        return StatusByColumn(
            all=status_paths,
            dirs=status_dirs,
            files=status_files,
            n_dirs=n_dirs,
            ns_dirs=ns_dirs,
            space_dirs=space_dirs,
            space_files=space_files,
        )
