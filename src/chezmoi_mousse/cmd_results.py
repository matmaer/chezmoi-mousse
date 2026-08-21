from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from chezmoi_mousse.named_tuples import CommandResult

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson

__all__ = ("CmdResults",)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangedPaths:
    added_managed: list[Path] = field(default_factory=lambda: [])
    changed_status: dict[Path, tuple[str, str]] = field(default_factory=lambda: {})
    removed_managed: list[Path] = field(default_factory=lambda: [])

    @property
    def added_managed_str(self) -> str:
        return "\n".join(str(p) for p in self.added_managed)

    @property
    def changed_status_str(self) -> str:
        return "\n".join(
            f"{p}:\nold status pair: '{old}' -> new status pair: '{new}'"
            for p, (old, new) in self.changed_status.items()
        )

    @property
    def removed_managed_str(self) -> str:
        return "\n".join(str(p) for p in self.removed_managed)

    @property
    def no_changes(self) -> bool:
        return (
            not self.added_managed
            and not self.changed_status
            and not self.removed_managed
        )  # Empty lists and dicts are falsy


@dataclass(slots=True, frozen=True)
class ResultsSnapshot:
    managed_paths: set[Path] = field(default_factory=lambda: set())
    status_paths: dict[Path, str] = field(default_factory=lambda: {})


class CmdResults:
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
    parsed_dump_config: ClassVar[ParsedJson]
    parsed_template_data: ClassVar[ParsedJson]

    # Store a snapshot which we can compare with new values in the result fields
    _managed_snapshot: ClassVar[ResultsSnapshot] = ResultsSnapshot()
    # To retrieve the current changes, updated by store_changed_paths
    changed_paths: ClassVar[ChangedPaths] = ChangedPaths()

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
        return Path(CmdResults.parsed_dump_config["destDir"])

    @classmethod
    def _create_results_snapshot(cls) -> ResultsSnapshot:
        managed_dirs = cls.managed_dirs_result.std_out.splitlines()
        managed_files = cls.managed_files_result.std_out.splitlines()
        status_dirs = cls.status_dirs_result.std_out.splitlines()
        status_files = cls.status_files_result.std_out.splitlines()

        return ResultsSnapshot(
            managed_paths={Path(line) for line in managed_dirs + managed_files if line},
            status_paths={
                Path(line[3:]): line[:2] for line in status_dirs + status_files
            },
        )

    @classmethod
    def store_current_snapshot(cls) -> None:
        cls._managed_snapshot = cls._create_results_snapshot()

    @classmethod
    def update_changed_paths(cls) -> None:
        new_snapshot = cls._create_results_snapshot()
        removed_managed = (
            cls._managed_snapshot.managed_paths - new_snapshot.managed_paths
        )
        added_managed = new_snapshot.managed_paths - cls._managed_snapshot.managed_paths

        changed_status: dict[Path, tuple[str, str]] = {}

        # Check for status changes among all paths that remained managed
        intersection = cls._managed_snapshot.managed_paths & new_snapshot.managed_paths

        for path in intersection:
            # Missing paths in status_pairs default to "  " (unchanged)
            old_code = cls._managed_snapshot.status_paths.get(path, "  ")
            new_code = new_snapshot.status_paths.get(path, "  ")

            if old_code != new_code:
                changed_status[path] = (old_code, new_code)

        cls.changed_paths = ChangedPaths(
            added_managed=sorted(added_managed),
            changed_status=changed_status,
            removed_managed=sorted(removed_managed),
        )
