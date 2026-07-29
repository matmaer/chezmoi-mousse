from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, ClassVar, NamedTuple, cast

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.cm_command import ReadCmd
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import PathKind, StatusCode

    type DirPathDict = dict[Path, list[ScanDirItem] | PathKind]
    type ParsedJson = dict[str, Any]
    type PathKindDict = dict[Path, PathKind]
    type StatusDict = dict[Path, StatusCode]
    type StrTup = tuple[str, ...]

__all__ = [
    "typed_lru_cache",
    "AppIds",
    "ChezmoiGui",
    "CmdResultCollector",
    "ManagedResults",
    "ParsedJson",
    "SplashResults",
    "StatusDict",
]


def typed_lru_cache[**FuncParams, FuncReturn](
    *, maxsize: int | None = 128, typed: bool = False
) -> Callable[[Callable[FuncParams, FuncReturn]], Callable[FuncParams, FuncReturn]]:
    def decorator(
        func: Callable[FuncParams, FuncReturn],
    ) -> Callable[FuncParams, FuncReturn]:
        return cast(
            Callable[FuncParams, FuncReturn],
            lru_cache(maxsize=maxsize, typed=typed)(func),
        )

    return decorator


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandResult:
    dry_run: bool
    err_lines: list[str]
    full_cmd_str: str
    out_lines: list[str]
    path_arg: Path | None
    pretty_cmd: str
    returncode: int
    std_err: str
    std_out: str
    time_stamp: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedResults:
    dest_dir: Path
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult


class ReadCmdGroups(NamedTuple):
    splash_only: list[ReadCmd]
    json_output: list[ReadCmd]
    managed: list[ReadCmd]

    @property
    def commands_count(self) -> int:
        return len(self.splash_only + self.json_output + self.managed)


class ScanDirItem(NamedTuple):
    # matches the argument passed to the os_scan_dir function
    parent_path: Path
    managed_arg: bool
    # absolute path matchingthe DirEntry.path attribute
    path: Path
    # matches DirEntry attribute
    is_dir: bool
    is_file: bool
    is_junction: bool
    is_symlink: bool
    name: str
    size: int
    # set by the os_scan_dir function
    sibling_count: int
    matches_unwanted: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class SplashResults:
    doctor: CommandResult
    git_log: CommandResult
    dump_config: CommandResult
    cat_config: CommandResult
    template_data: CommandResult
    ignored: CommandResult
    git_remote: CommandResult
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult

    @property
    def results_list(self) -> list[CommandResult]:
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


class CmdResultCollector:

    dest_dir: ClassVar[Path]
    cat_config: ClassVar[CommandResult]
    dest_dir: ClassVar[Path]
    doctor: ClassVar[CommandResult]
    dump_config: ClassVar[CommandResult]
    git_log: ClassVar[CommandResult]
    git_remote: ClassVar[CommandResult]
    ignored: ClassVar[CommandResult]
    managed_dirs: ClassVar[CommandResult]
    managed_files: ClassVar[CommandResult]
    parsed_dump_config: ClassVar[ParsedJson]
    parsed_template_data: ClassVar[ParsedJson]
    status_dirs: ClassVar[CommandResult]
    status_files: ClassVar[CommandResult]
    template_data: ClassVar[CommandResult]

    @classmethod
    def get_splash_results(cls) -> SplashResults:
        return SplashResults(
            cat_config=cls.cat_config,
            doctor=cls.doctor,
            dump_config=cls.dump_config,
            git_log=cls.git_log,
            git_remote=cls.git_remote,
            ignored=cls.ignored,
            managed_dirs=cls.managed_dirs,
            managed_files=cls.managed_files,
            status_dirs=cls.status_dirs,
            status_files=cls.status_files,
            template_data=cls.template_data,
        )

    # get the managed results as a ManagedResults tuple
    @classmethod
    def get_managed_results(cls) -> ManagedResults:
        return ManagedResults(
            dest_dir=cls.dest_dir,
            managed_dirs=cls.managed_dirs,
            managed_files=cls.managed_files,
            status_dirs=cls.status_dirs,
            status_files=cls.status_files,
        )
