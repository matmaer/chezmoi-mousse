from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.cm_command import ReadCmd
    from chezmoi_mousse.cm_types import PathKindMap, StatusMap


__all__ = [
    "CommandResult",
    "ManagedResults",
    "ManagedTreePaths",
    "ReadCmdGroups",
    "ScanDirItem",
]


class CommandResult(NamedTuple):
    dry_run: bool | None
    err_lines: list[str]
    full_cmd_str: str
    out_lines: list[str]
    path_arg: Path | None
    pretty_cmd: str
    returncode: int
    std_err: str
    std_out: str
    time_stamp: str


class ManagedResults(NamedTuple):
    dest_dir: Path
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult


class ManagedTreePaths(NamedTuple):
    dest_dir: Path
    managed_dirs_map: PathKindMap
    managed_files_map: PathKindMap
    n_dirs: frozenset[Path]
    no_managed_paths: bool
    no_status_paths: bool
    status_dirs_map: StatusMap
    status_files_map: StatusMap
    tree_status_dirs: frozenset[Path]
    unchanged_dirs: frozenset[Path]
    unchanged_files: frozenset[Path]


class ReadCmdGroups(NamedTuple):
    splash_only: list[ReadCmd]
    json_output: list[ReadCmd]
    managed: list[ReadCmd]

    @property
    def commands_count(self) -> int:
        return len(self.splash_only + self.json_output + self.managed)


class ScanDirItem(NamedTuple):
    # matches the argument passed to the os_scan_dir function
    scanned_dir: Path
    managed_arg: bool
    # absolute path matchingthe DirEntry.path attribute
    path: Path
    # matches DirEntry attribute
    is_dir: bool
    is_file: bool
    is_symlink: bool
    name: str
    # if it's a dir or if an exception occurs when calling .stat()
    file_size: int | None
    # set by the os_scan_dir function
    sibling_count: int
    matches_unwanted: bool
