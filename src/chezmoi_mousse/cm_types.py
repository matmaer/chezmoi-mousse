from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import TYPE_CHECKING, ClassVar, NamedTuple, cast

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.cm_command import ReadCmd
    from chezmoi_mousse.str_enums import PathKind, StatusCode
    from chezmoi_mousse.textual_app import ChezmoiGui

    type StatusDict = dict[Path, StatusCode]
    type PathKindDict = dict[Path, PathKind]
    type StrTup = tuple[str, ...]
    type ParsedJson = dict[str, Any]

__all__ = [
    "typed_lru_cache",
    "AppIds",
    "ChezmoiGui",
    "CmdResultCollector",
    "ManagedResults",
    "ParsedConfig",
    "ParsedJson",
    "SplashResults",
    "StatusDict",
    "TabIds",
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


class CommandResult(NamedTuple):
    dry_run: bool
    err_lines: list[str]
    full_cmd_str: str
    out_lines: list[str]
    path_arg: Path | None
    pretty_cmd: str
    returncode: int
    std_err: str
    std_out: str
    colored_cmd: str


class ManagedResults(NamedTuple):
    dest_dir: Path
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult
    unmanaged_dirs: CommandResult
    unmanaged_files: CommandResult


class ParsedConfig(NamedTuple):
    dest_dir: Path
    auto_add: bool
    auto_commit: bool
    auto_push: bool


class ReadCmdGroups(NamedTuple):
    splash_only: list[ReadCmd]
    json_output: list[ReadCmd]
    managed: list[ReadCmd]

    @property
    def commands_count(self) -> int:
        return len(self.splash_only + self.json_output + self.managed)


class SplashResults(NamedTuple):
    dest_dir: Path
    doctor: CommandResult
    git_log: CommandResult
    dump_config: CommandResult
    cat_config: CommandResult
    template_data: CommandResult
    ignored: CommandResult
    git_remote: CommandResult
    managed_dirs: CommandResult
    managed_files: CommandResult
    parsed_dump_config: ParsedJson
    parsed_template_data: ParsedJson
    status_dirs: CommandResult
    status_files: CommandResult
    unmanaged_dirs: CommandResult
    unmanaged_files: CommandResult


class TabIds(NamedTuple):
    add: AppIds
    apply: AppIds
    config: AppIds
    debug: AppIds
    logs: AppIds
    re_add: AppIds


class CmdResultCollector:

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
    unmanaged_dirs: ClassVar[CommandResult]
    unmanaged_files: ClassVar[CommandResult]

    @classmethod
    def get_all_results(cls) -> SplashResults:
        return SplashResults(
            dest_dir=cls.dest_dir,
            cat_config=cls.cat_config,
            doctor=cls.doctor,
            dump_config=cls.dump_config,
            git_log=cls.git_log,
            git_remote=cls.git_remote,
            ignored=cls.ignored,
            managed_dirs=cls.managed_dirs,
            managed_files=cls.managed_files,
            parsed_dump_config=cls.parsed_dump_config,
            parsed_template_data=cls.parsed_template_data,
            status_dirs=cls.status_dirs,
            status_files=cls.status_files,
            template_data=cls.template_data,
            unmanaged_dirs=cls.unmanaged_dirs,
            unmanaged_files=cls.unmanaged_files,
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
            unmanaged_dirs=cls.unmanaged_dirs,
            unmanaged_files=cls.unmanaged_files,
        )
