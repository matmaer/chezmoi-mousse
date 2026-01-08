from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ._str_enums import StatusCode

if TYPE_CHECKING:
    from ._chezmoi_command import CommandResult

type PathDict = dict[Path, str]

__all__ = ["ChezmoiPaths", "PathDict"]


@dataclass(slots=True)
class PathData:
    found: bool
    status: StatusCode


@dataclass(slots=True)
class DirData:
    found: bool
    status: StatusCode
    files: dict[Path, PathData] = field(default_factory=dict[Path, PathData])


@dataclass(slots=True)
class ChezmoiPaths:
    dest_dir: Path
    managed_dirs_result: CommandResult
    managed_files_result: CommandResult
    status_dirs_result: CommandResult
    status_files_result: CommandResult

    dirs: "list[Path]" = field(default_factory=list[Path], init=False)
    files: "list[Path]" = field(default_factory=list[Path], init=False)
    status_files: "PathDict" = field(
        default_factory=dict[Path, str], init=False
    )
    no_status_files: "PathDict" = field(
        default_factory=dict[Path, str], init=False
    )  # In use to populate listTree in gui/common/trees.py

    apply_dirs: "dict[Path, DirData]" = field(
        default_factory=dict[Path, DirData], init=False
    )
    apply_status_files: "PathDict" = field(init=False)
    apply_status_dirs: "PathDict" = field(init=False)
    _apply_status_paths: "PathDict" = field(init=False)
    re_add_dirs: "dict[Path, DirData]" = field(
        default_factory=dict[Path, DirData], init=False
    )
    re_add_status_files: "PathDict" = field(
        default_factory=dict[Path, str], init=False
    )
    re_add_status_dirs: "PathDict" = field(
        default_factory=dict[Path, str], init=False
    )
    _re_add_status_paths: "PathDict" = field(
        default_factory=dict[Path, str], init=False
    )
    _status_dirs: "PathDict" = field(
        default_factory=dict[Path, str], init=False
    )

    def __post_init__(self) -> None:
        self._update_managed_paths()
        self._update_status_paths()

        for dir_path in self.dirs:
            # Populate apply_dirs
            apply_status = StatusCode(
                self.apply_status_dirs.get(dir_path, StatusCode.fake_no_status)
            )
            apply_files: dict[Path, PathData] = {}
            for file_path in self.files:
                if file_path.parent == dir_path:
                    status = self.apply_status_files.get(
                        file_path, StatusCode.fake_no_status
                    )
                    apply_files[file_path] = PathData(
                        found=file_path.exists(), status=StatusCode(status)
                    )
            self.apply_dirs[dir_path] = DirData(
                found=dir_path.exists(), status=apply_status, files=apply_files
            )

            # Populate re_add_dirs
            re_add_status = StatusCode(
                self.re_add_status_dirs.get(
                    dir_path, StatusCode.fake_no_status
                )
            )
            re_add_files: dict[Path, PathData] = {}
            for file_path in self.files:
                if file_path.parent == dir_path:
                    status = self.re_add_status_files.get(
                        file_path, StatusCode.fake_no_status
                    )
                    re_add_files[file_path] = PathData(
                        found=file_path.exists(), status=StatusCode(status)
                    )
            self.re_add_dirs[dir_path] = DirData(
                found=dir_path.exists(),
                status=re_add_status,
                files=re_add_files,
            )

    def _update_managed_paths(self) -> None:
        self.dirs = [self.dest_dir] + [
            Path(line)
            for line in self.managed_dirs_result.std_out.splitlines()
        ]
        self.files = [
            Path(line)
            for line in self.managed_files_result.std_out.splitlines()
        ]

    def _update_status_paths(self) -> None:
        # Populate cache used by both apply and re-add
        self._status_dirs = {
            Path(line[3:]): line[:2]
            for line in self.status_dirs_result.std_out.splitlines()
            if line.strip() != ""
        }
        self.status_files: "PathDict" = {
            Path(line[3:]): line[:2]
            for line in self.status_files_result.std_out.splitlines()
            if line.strip() != ""
        }
        self.no_status_files = {
            path: StatusCode.fake_no_status
            for path in self.files
            if path not in self.status_files.keys()
        }
        # Populate apply related status paths
        self.apply_status_files = {
            path: status_pair[1]
            for path, status_pair in self.status_files.items()
            if status_pair[1]  # Check second character only
            in (StatusCode.Added, StatusCode.Deleted, StatusCode.Modified)
        }
        real_apply_status_dirs = {
            path: status_pair[1]
            for path, status_pair in self._status_dirs.items()
            if status_pair[1]  # Check second character only
            in (StatusCode.Added, StatusCode.Deleted, StatusCode.Modified)
        }
        dirs_with_status_files = {
            file_path.parent: StatusCode.No_Change
            for file_path, _ in self.apply_status_files.items()
            if file_path.parent not in real_apply_status_dirs
        }
        self.apply_status_dirs = {
            **real_apply_status_dirs,
            **dirs_with_status_files,
        }
        self._apply_status_paths = {
            **self.apply_status_dirs,
            **self.apply_status_files,
        }

        # Populate re-add related status paths

        # Dir status is not relevant to the re-add command, just return any
        # parent dir that contains re-add status files
        # Return those directories with status StatusCode.fake_no_status
        # No need to check for existence, as files within must exist
        self.re_add_status_files = {
            path: status_pair[0]
            for path, status_pair in self.status_files.items()
            if (
                status_pair[0] == StatusCode.Modified
                # consider some files to have a status as re-add can be run
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
        self.re_add_status_dirs = {
            file_path.parent: StatusCode.fake_no_status
            for file_path in self.re_add_status_files.keys()
        }
        self._re_add_status_paths = {
            **self.re_add_status_dirs,
            **self.re_add_status_files,
        }

    def apply_status_dirs_in(self, dir_path: Path) -> PathDict:
        return {
            path: self.apply_dirs[path].status
            for path in self.apply_dirs
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
            path: self.re_add_dirs[path].status
            for path in self.re_add_dirs
            if path.parent == dir_path
        }

    def apply_files_without_status_in(self, dir_path: Path) -> PathDict:
        return {
            path: pathdata.status
            for path, pathdata in self.apply_dirs[dir_path].files.items()
            if pathdata.status
            in (StatusCode.fake_no_status, StatusCode.No_Change)
        }

    def re_add_files_without_status_in(self, dir_path: Path) -> PathDict:
        return {
            path: pathdata.status
            for path, pathdata in self.re_add_dirs[dir_path].files.items()
            if pathdata.status
            in (StatusCode.fake_no_status, StatusCode.No_Change)
        }

    def has_apply_status_paths_in(self, dir_path: Path) -> bool:
        # Return True if any apply-status path is a descendant of the
        # provided directory.
        return any(
            status_path.is_relative_to(dir_path)
            for status_path in self._apply_status_paths.keys()
        )

    def has_re_add_status_paths_in(self, dir_path: Path) -> bool:
        # Same logic as for apply: return True if any re-add status path
        # is a descendant of dir_path.
        return any(
            status_path.is_relative_to(dir_path)
            for status_path in self._re_add_status_paths.keys()
        )

    def list_apply_status_paths_in(self, dir_path: Path) -> PathDict:
        # Return a dict of apply-status paths that are descendants of the
        # provided directory, mapping path -> status.
        return {
            path: status
            for path, status in self._apply_status_paths.items()
            if path.is_relative_to(dir_path)
        }

    def list_re_add_status_paths_in(self, dir_path: Path) -> PathDict:
        # Return a dict of re-add-status paths that are descendants of dir_path,
        # mapping path -> status.
        return {
            path: status
            for path, status in self._re_add_status_paths.items()
            if path.is_relative_to(dir_path)
        }
