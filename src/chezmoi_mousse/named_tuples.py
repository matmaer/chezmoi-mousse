from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from chezmoi_mousse.str_enums import ReadCmd, WriteCmd

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.cm_types import PathKindMap, StatusMap


__all__ = [
    "AffectedPaths",
    "CommandResult",
    "ManagedTreePaths",
    "ParsedDumpConfig",
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
        return "\n".join(str(p) for p in self.paths)


class CommandResult(NamedTuple):
    cmd_enum: WriteCmd | ReadCmd | None
    full_cmd: str
    path_arg: Path | None
    pretty_cmd: str
    returncode: int
    std_err: str
    std_out: str
    time_stamp: str

    @classmethod
    def empty(cls) -> CommandResult:
        return cls(
            cmd_enum=None,
            full_cmd="",
            path_arg=None,
            pretty_cmd="",
            returncode=0,
            std_err="",
            std_out="",
            time_stamp="",
        )


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


class ParsedDumpConfig(NamedTuple):
    dest_dir_path: Path | None = None
    auto_add_bool: bool | None = None
    auto_commit_bool: bool | None = None
    auto_push_bool: bool | None = None

    @property
    def dest_dir(self) -> Path:
        if self.dest_dir_path is None:
            raise RuntimeError("Accessing dest_dir before the config is parsed")
        return self.dest_dir_path

    @property
    def auto_add(self) -> bool:
        if self.auto_add_bool is None:
            raise RuntimeError("Accessing auto_add before the config is parsed")
        return self.auto_add_bool

    @property
    def auto_commit(self) -> bool:
        if self.auto_commit_bool is None:
            raise RuntimeError("Accessing auto_commit before the config is parsed")
        return self.auto_commit_bool

    @property
    def auto_push(self) -> bool:
        if self.auto_push_bool is None:
            raise RuntimeError("Accessing auto_push before the config is parsed")
        return self.auto_push_bool


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
