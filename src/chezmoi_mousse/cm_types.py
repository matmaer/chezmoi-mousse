from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, lru_cache
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
    "AppIds",
    "ChezmoiGui",
    "CmdResultCollector",
    "ManagedResults",
    "ParsedJson",
    "SplashResults",
    "StatusDict",
    "TabIds",
    "typed_lru_cache",
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


@dataclass(frozen=True, kw_only=True)
class ManagedPaths:
    managed_dirs: PathKindDict
    managed_files: PathKindDict

    apply_dirs: StatusDict
    apply_files: StatusDict
    re_add_dirs: StatusDict
    re_add_files: StatusDict

    apply_n_dirs: PathKindDict
    re_add_n_dirs: PathKindDict

    unmanaged_dirs: PathKindDict
    unmanaged_files: PathKindDict

    @cached_property
    def no_apply_paths(self) -> bool:
        return not self.apply_dirs and not self.apply_files

    @cached_property
    def no_re_add_paths(self) -> bool:
        return not self.re_add_dirs and not self.re_add_files

    @cached_property
    def no_status_paths(self) -> bool:
        return self.no_apply_paths and self.no_re_add_paths

    @cached_property
    def no_managed_paths(self) -> bool:
        return not self.managed_dirs and not self.managed_files


class CommandResult(NamedTuple):
    dry_run: bool
    err_lines: list[str]
    full_cmd_str: str
    out_lines: list[str]
    parsed_json: ParsedJson | None
    path_arg: Path | None
    pretty_cmd: str
    returncode: int
    std_err: str
    std_out: str
    colored_cmd: str


class ManagedResults(NamedTuple):
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult
    unmanaged_dirs: CommandResult
    unmanaged_files: CommandResult


class ParsedJsonResults(NamedTuple):
    dump_config: CommandResult
    template_data: CommandResult


class ReadCmdGroups(NamedTuple):
    splash_only: list[ReadCmd]
    json_output: list[ReadCmd]
    managed: list[ReadCmd]

    @property
    def commands_count(self) -> int:
        return len(self.splash_only + self.json_output + self.managed)


class SplashResults(NamedTuple):
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

    # currently only executed in splash screen
    doctor: ClassVar[CommandResult]
    git_log: ClassVar[CommandResult]
    dump_config: ClassVar[CommandResult]
    cat_config: ClassVar[CommandResult]
    template_data: ClassVar[CommandResult]
    ignored: ClassVar[CommandResult]
    git_remote: ClassVar[CommandResult]

    # currently executed in both splash screen and loading screen
    managed_dirs: ClassVar[CommandResult]
    managed_files: ClassVar[CommandResult]
    status_dirs: ClassVar[CommandResult]
    status_files: ClassVar[CommandResult]
    unmanaged_dirs: ClassVar[CommandResult]
    unmanaged_files: ClassVar[CommandResult]

    @classmethod
    def get_all_results(cls) -> SplashResults:
        return SplashResults(
            doctor=cls.doctor,
            git_log=cls.git_log,
            dump_config=cls.dump_config,
            cat_config=cls.cat_config,
            template_data=cls.template_data,
            ignored=cls.ignored,
            git_remote=cls.git_remote,
            managed_dirs=cls.managed_dirs,
            managed_files=cls.managed_files,
            status_dirs=cls.status_dirs,
            status_files=cls.status_files,
            unmanaged_dirs=cls.unmanaged_dirs,
            unmanaged_files=cls.unmanaged_files,
        )

    # get the managed results as a ManagedResults tuple
    @classmethod
    def get_parsed_json_results(cls) -> ParsedJsonResults:
        return ParsedJsonResults(
            dump_config=cls.dump_config, template_data=cls.template_data
        )

    # get the managed results as a ManagedResults tuple
    @classmethod
    def get_managed_results(cls) -> ManagedResults:
        return ManagedResults(
            managed_dirs=cls.managed_dirs,
            managed_files=cls.managed_files,
            status_dirs=cls.status_dirs,
            status_files=cls.status_files,
            unmanaged_dirs=cls.unmanaged_dirs,
            unmanaged_files=cls.unmanaged_files,
        )
