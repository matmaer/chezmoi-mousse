from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from chezmoi_mousse.named_tuples import CommandResult

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson

__all__ = ("ResultCollector",)


@dataclass(slots=True, frozen=True)
class ManagedSnapshot:
    managed_dirs: set[Path]
    managed_files: set[Path]
    status_dirs: set[str]
    status_files: set[str]


class ResultCollector:
    # chezmoi ReadCmd results which do not require arguments or which require the path
    # arg to be None if ran on the dest dir, eg git_log
    cat_config_result: ClassVar[CommandResult]
    doctor_result: ClassVar[CommandResult]
    dump_config_result: ClassVar[CommandResult]
    git_log_result: ClassVar[CommandResult]
    git_remote_result: ClassVar[CommandResult]
    ignored_result: ClassVar[CommandResult]
    managed_dirs_result: ClassVar[CommandResult]
    managed_files_result: ClassVar[CommandResult]
    status_dirs_result: ClassVar[CommandResult]
    status_files_result: ClassVar[CommandResult]
    template_data_result: ClassVar[CommandResult]

    # Processed json results in SplashScreen
    parsed_dump_config: ParsedJson
    parsed_template_data: ParsedJson

    # Keep track of the selected path by tab
    add_path: ClassVar[Path]
    apply_path: ClassVar[Path]
    re_add_path: ClassVar[Path]

    # Used for logging after the splash screen is disimissed and we push the MainScreen
    @classmethod
    def splash_results(cls) -> list[CommandResult]:
        return [
            cls.cat_config_result,
            cls.doctor_result,
            cls.dump_config_result,
            cls.git_log_result,
            cls.git_remote_result,
            cls.ignored_result,
            cls.managed_dirs_result,
            cls.managed_files_result,
            cls.status_dirs_result,
            cls.status_files_result,
            cls.template_data_result,
        ]

    # Used to retrieve results after the 'Refresh Tree' button was clicked
    @classmethod
    def managed_cmd_results(cls) -> list[CommandResult]:
        return [
            cls.managed_dirs_result,
            cls.managed_files_result,
            cls.status_dirs_result,
            cls.status_files_result,
        ]

    @classmethod
    def get_dest_dir(cls) -> Path:
        return Path(ResultCollector.parsed_dump_config["destDir"])

    @classmethod
    def get_managed_results_snapshot(cls) -> Path:
        return Path(ResultCollector.parsed_dump_config["destDir"])
