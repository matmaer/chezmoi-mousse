from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, NamedTuple, cast

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import MappingProxyType
    from typing import Any

    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.cm_attributes import ManagedPaths
    from chezmoi_mousse.cm_command import ReadCmd
    from chezmoi_mousse.str_enums import PathKind, StatusCode

    type ParsedJson = dict[str, Any]
    type PathDataDict = dict[Path, PathKind | ScanDirItem]
    type PathKindDict = dict[Path, PathKind]
    type PathKindMap = MappingProxyType[Path, PathKind]
    type StatusDict = dict[Path, StatusCode]
    type StatusMap = MappingProxyType[Path, StatusCode]
    type StrTuple = tuple[str, ...]
    type TreeNodeDict = dict[Path, TreeNode[Path]]


def typed_lru_cache[**FuncParams, FuncReturn](
    *, maxsize: int | None = 128, typed: bool = False
) -> Callable[[Callable[FuncParams, FuncReturn]], Callable[FuncParams, FuncReturn]]:
    def decorator(
        func: Callable[FuncParams, FuncReturn],
    ) -> Callable[FuncParams, FuncReturn]:
        return cast(
            # has to be quoted for cast if don't want to import Callable at runtime
            "Callable[FuncParams, FuncReturn]",
            lru_cache(maxsize=maxsize, typed=typed)(func),
        )

    return decorator


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandResult:
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


@dataclass(slots=True)
class ResultCollector:

    dest_dir: Path = field(init=False)
    cat_config: CommandResult = field(init=False)
    doctor: CommandResult = field(init=False)
    dump_config: CommandResult = field(init=False)
    git_log: CommandResult = field(init=False)
    git_remote: CommandResult = field(init=False)
    ignored: CommandResult = field(init=False)
    managed_dirs: CommandResult = field(init=False)
    managed_files: CommandResult = field(init=False)
    parsed_dump_config: ParsedJson = field(init=False)
    parsed_template_data: ParsedJson = field(init=False)
    status_dirs: CommandResult = field(init=False)
    status_files: CommandResult = field(init=False)
    template_data: CommandResult = field(init=False)
    managed_paths_instance: ManagedPaths = field(init=False)

    # Used for logging after the splash screen is disimissed and we push the MainScreen
    @property
    def splash_results_list(self) -> list[CommandResult]:
        return [
            self.doctor,
            self.git_log,
            self.dump_config,
            self.cat_config,
            self.template_data,
            self.ignored,
            self.git_remote,
            self.managed_dirs,
            self.managed_files,
            self.status_dirs,
            self.status_files,
        ]
