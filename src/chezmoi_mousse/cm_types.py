from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, ClassVar, NamedTuple

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.cm_command import ReadCmd, WriteCmd
    from chezmoi_mousse.str_enums import PathKind, StatusCode
    from chezmoi_mousse.textual_app import ChezmoiGui

    type StatusDict = dict[Path, StatusCode]
    type PathKindDict = dict[Path, PathKind]
    type StrTup = tuple[str, ...]
    type ParsedJson = dict[str, Any]

__all__ = [
    "CmdResultCollector",
    "ManagedResults",
    "ParsedJson",
    "SplashResults",
    "StatusDict",
    # exports only importable in TYPE_CHECKING block
    "AppIds",
    "ChezmoiGui",
    "TabIds",
]


class TabIds(NamedTuple):
    add: AppIds
    apply: AppIds
    config: AppIds
    debug: AppIds
    logs: AppIds
    re_add: AppIds


@dataclass(slots=True, frozen=True, kw_only=True)
class CommandResult:
    dry_run: bool
    err_lines: list[str]
    full_cmd_str: str
    out_lines: list[str]
    parsed_json: ParsedJson
    path_arg: Path | None
    returncode: int
    std_err: str
    std_out: str
    verb_cmd: ReadCmd | WriteCmd


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


class ManagedResults(NamedTuple):
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult
    unmanaged_dirs: CommandResult
    unmanaged_files: CommandResult


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
    def get_managed_results(cls) -> ManagedResults:
        return ManagedResults(
            managed_dirs=cls.managed_dirs,
            managed_files=cls.managed_files,
            status_dirs=cls.status_dirs,
            status_files=cls.status_files,
            unmanaged_dirs=cls.unmanaged_dirs,
            unmanaged_files=cls.unmanaged_files,
        )
