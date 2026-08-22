from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.cm_types import PathKindMap, StatusMap


__all__ = [
    "AffectedPaths",
    "CommandResult",
    "ManagedTreePaths",
    "PwMgrData",
    "RunCommandInfo",
    "ScanDirItem",
    "SwitchData",
]


class AffectedPaths(NamedTuple):
    paths: list[Path]
    pretty_cmd: str
    std_err: str

    @property
    def path_strings(self) -> str:
        return " ".join(str(p) for p in self.paths)


class CommandResult(NamedTuple):
    full_cmd: str
    path_arg: Path | None
    pretty_cmd: str
    returncode: int
    std_err: str
    std_out: str
    time_stamp: str


class ManagedTreePaths(NamedTuple):
    managed_dirs: PathKindMap
    managed_files: PathKindMap
    n_dirs: frozenset[Path]
    no_status_paths: bool
    status_dirs: StatusMap
    status_files: StatusMap
    tree_status_dirs: StatusMap
    unchanged_dirs: frozenset[Path]
    unchanged_files: frozenset[Path]
    unchanged_tree_dirs: frozenset[Path]

    @property
    def status_paths_set(self) -> frozenset[Path]:
        return frozenset(self.status_dirs | self.status_files)


class RunCommandInfo(NamedTuple):
    border_title: str
    border_subtitle: str
    cmd_description: str


class PwMgrData(NamedTuple):
    description: str
    doctor_check: str
    link: str
    info: str


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


class SwitchData(NamedTuple):
    label: str
    enabled_tooltip: str
