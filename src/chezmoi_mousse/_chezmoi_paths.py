from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ._str_enum_names import StatusCode

if TYPE_CHECKING:
    from ._chezmoi_command import CommandResult
    from ._type_checking import PathDict, PathList


__all__ = ["ChezmoiPaths"]


@dataclass(slots=True)
class ChezmoiPaths:

    managed_dirs_result: CommandResult
    managed_files_result: CommandResult
    status_dirs_result: CommandResult
    status_files_result: CommandResult

    @property
    def dirs(self) -> PathList:
        return [
            Path(line)
            for line in self.managed_dirs_result.std_out.splitlines()
        ]

    @property
    def files(self) -> PathList:
        return [
            Path(line)
            for line in self.managed_files_result.std_out.splitlines()
        ]

    @property
    def status_dirs(self) -> PathDict:
        return {
            Path(line[3:]): line[:2]
            for line in self.status_dirs_result.std_out.splitlines()
            if line.strip() != ""
        }

    @property
    def status_files(self) -> PathDict:
        return {
            Path(line[3:]): line[:2]
            for line in self.status_files_result.std_out.splitlines()
            if line.strip() != ""
        }

    @property
    def all_status_paths(self) -> PathDict:
        return {**self.status_dirs, **self.status_files}

    # properties filtering status files into apply and re-add contexts

    @property
    def apply_status_files(self) -> PathDict:
        return {
            path: status_pair[1]
            for path, status_pair in self.status_files.items()
            if status_pair[1]  # Check second character only
            in (StatusCode.Added, StatusCode.Deleted, StatusCode.Modified)
        }

    @property
    def re_add_status_files(self) -> PathDict:
        # consider these files to have a status as chezmoi re-add can be run
        return {
            path: status_pair[0]
            for path, status_pair in self.status_files.items()
            if (
                status_pair[0] == StatusCode.Modified
                or (
                    status_pair[0] == StatusCode.No_Change
                    and status_pair[1]
                    in (
                        StatusCode.Added,
                        StatusCode.Deleted,
                        StatusCode.Modified,
                    )
                )
            )
            and path.exists()
        }

    # properties filtering status dirs into apply and re-add contexts

    @property
    def apply_status_dirs(self) -> PathDict:
        real_status_dirs = {
            path: status_pair[1]
            for path, status_pair in self.status_dirs.items()
            if status_pair[1]  # Check second character only
            in (StatusCode.Added, StatusCode.Deleted, StatusCode.Modified)
        }
        dirs_with_status_files = {
            file_path.parent: StatusCode.No_Change
            for file_path, _ in self.apply_status_files.items()
            if file_path.parent not in real_status_dirs
        }
        return {**real_status_dirs, **dirs_with_status_files}

    @property
    def re_add_status_dirs(self) -> PathDict:
        # Dir status is not relevant to the re-add command, just return any
        # parent dir that contains re-add status files
        # Return those directories with status StatusCode.fake_no_status
        # No need to check for existence, as files within must exist
        return {
            file_path.parent: StatusCode.fake_no_status
            for file_path in self.re_add_status_files.keys()
        }

    # properties for files without status
    @property
    def apply_files_without_status(self) -> PathDict:
        return {
            path: StatusCode.fake_no_status
            for path in self.files
            if path not in self.apply_status_files.keys()
        }

    @property
    def re_add_files_without_status(self) -> PathDict:
        return {
            path: StatusCode.fake_no_status
            for path in self.files
            if path not in self.re_add_status_files.keys()
        }

    # concat dicts, files override dirs on key collisions, should never happen
    @property
    def apply_status_paths(self) -> PathDict:
        return {**self.apply_status_dirs, **self.apply_status_files}

    @property
    def re_add_status_paths(self) -> PathDict:
        return {**self.re_add_status_dirs, **self.re_add_status_files}

    def apply_status_dirs_in(self, dir_path: Path) -> PathDict:
        return {
            path: status
            for path, status in self.apply_status_dirs.items()
            if path.parent == dir_path
        }

    def apply_status_files_in(self, dir_path: Path) -> PathDict:
        return {
            path: status
            for path, status in self.apply_status_files.items()
            if path.parent == dir_path
        }

    def re_add_status_files_in(self, dir_path: Path) -> PathDict:
        return {
            path: status
            for path, status in self.re_add_status_files.items()
            if path.parent == dir_path
        }

    def re_add_status_dirs_in(self, dir_path: Path) -> PathDict:
        return {
            path: status
            for path, status in self.re_add_status_dirs.items()
            if path.parent == dir_path
        }

    def apply_files_without_status_in(self, dir_path: Path) -> PathDict:
        return {
            path: status
            for path, status in self.apply_files_without_status.items()
            if path.parent == dir_path
        }

    def re_add_files_without_status_in(self, dir_path: Path) -> PathDict:
        return {
            path: status
            for path, status in self.re_add_files_without_status.items()
            if path.parent == dir_path
        }

    def has_apply_status_paths_in(self, dir_path: Path) -> bool:
        # Return True if any apply-status path is a descendant of the
        # provided directory.
        return any(
            status_path.is_relative_to(dir_path)
            for status_path in self.apply_status_paths.keys()
        )

    def has_re_add_status_paths_in(self, dir_path: Path) -> bool:
        # Same logic as for apply: return True if any re-add status path
        # is a descendant of dir_path.
        return any(
            status_path.is_relative_to(dir_path)
            for status_path in self.re_add_status_paths.keys()
        )

    def list_apply_status_paths_in(self, dir_path: Path) -> PathDict:
        # Return a dict of apply-status paths that are descendants of the
        # provided directory, mapping path -> status.
        return {
            path: status
            for path, status in self.apply_status_paths.items()
            if path.is_relative_to(dir_path)
        }

    def list_re_add_status_paths_in(self, dir_path: Path) -> PathDict:
        # Return a dict of re-add-status paths that are descendants of dir_path,
        # mapping path -> status.
        return {
            path: status
            for path, status in self.re_add_status_paths.items()
            if path.is_relative_to(dir_path)
        }
