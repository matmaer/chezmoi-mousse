from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, ClassVar, NamedTuple

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.cm_command import CommandResult
    from chezmoi_mousse.str_enums import StatusCode
    from chezmoi_mousse.textual_app import ChezmoiGui

    type ParsedJson = dict[str, Any]
    type StatusDict = dict[Path, StatusCode]

__all__ = [
    "AllResults",
    "CmdResults",
    "ManagedResults",
    "SplashResults",
    # exports only importable in TYPE_CHECKING block
    "AppIds",
    "ChezmoiGui",
    "ParsedJson",
    "StatusDict",
]


class ManagedResults(NamedTuple):
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult
    unmanaged_dirs: CommandResult
    unmanaged_files: CommandResult


class SplashResults(NamedTuple):
    doctor_result: CommandResult
    git_log_result: CommandResult
    dump_config_result: CommandResult
    cat_config_result: CommandResult
    template_data_result: CommandResult
    ignored_result: CommandResult
    git_remote_result: CommandResult


class AllResults(NamedTuple):
    managed_results: ManagedResults
    splash_results: SplashResults


class CmdResults:

    # currently only executed in splash screen
    doctor_result: ClassVar[CommandResult]
    git_log_result: ClassVar[CommandResult]
    dump_config_result: ClassVar[CommandResult]
    cat_config_result: ClassVar[CommandResult]
    template_data_result: ClassVar[CommandResult]
    ignored_result: ClassVar[CommandResult]
    git_remote_result: ClassVar[CommandResult]

    # managed related commands
    managed_dirs_result: ClassVar[CommandResult]
    managed_files_result: ClassVar[CommandResult]
    status_dirs_result: ClassVar[CommandResult]
    status_files_result: ClassVar[CommandResult]
    unmanaged_dirs_result: ClassVar[CommandResult]
    unmanaged_files_result: ClassVar[CommandResult]

    # get the managed results as a ManagedResults tuple
    @classmethod
    def get_managed_results(cls) -> ManagedResults:
        return ManagedResults(
            managed_dirs=cls.managed_dirs_result,
            managed_files=cls.managed_files_result,
            status_dirs=cls.status_dirs_result,
            status_files=cls.status_files_result,
            unmanaged_dirs=cls.unmanaged_dirs_result,
            unmanaged_files=cls.unmanaged_files_result,
        )

    @classmethod
    def get_splash_results(cls) -> SplashResults:
        return SplashResults(
            doctor_result=cls.doctor_result,
            git_log_result=cls.git_log_result,
            dump_config_result=cls.dump_config_result,
            cat_config_result=cls.cat_config_result,
            template_data_result=cls.template_data_result,
            ignored_result=cls.ignored_result,
            git_remote_result=cls.git_remote_result,
        )

    @classmethod
    def get_all_results(cls) -> AllResults:
        return AllResults(
            managed_results=cls.get_managed_results(),
            splash_results=cls.get_splash_results(),
        )
