from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.named_tuples import CommandResult

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson


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
        )


@dataclass(slots=True, frozen=True)
class ResultsSnapshot:
    managed_paths: set[Path] = field(default_factory=lambda: set())
    status_paths: dict[Path, str] = field(default_factory=lambda: {})


EMPTY_CMD_RESULT = CommandResult(
    full_cmd="",
    path_arg=None,
    pretty_cmd="",
    returncode=0,
    std_err="",
    std_out="",
    time_stamp="",
)

cat_config_result: CommandResult = EMPTY_CMD_RESULT
doctor_result: CommandResult = EMPTY_CMD_RESULT
dump_config_result: CommandResult = EMPTY_CMD_RESULT
git_log_result: CommandResult = EMPTY_CMD_RESULT
git_remote_result: CommandResult = EMPTY_CMD_RESULT
ignored_result: CommandResult = EMPTY_CMD_RESULT
managed_dirs_result: CommandResult = EMPTY_CMD_RESULT
managed_files_result: CommandResult = EMPTY_CMD_RESULT
status_dirs_result: CommandResult = EMPTY_CMD_RESULT
status_files_result: CommandResult = EMPTY_CMD_RESULT
template_data_result: CommandResult = EMPTY_CMD_RESULT

parsed_dump_config: ParsedJson = {}
parsed_template_data: ParsedJson = {}

_managed_snapshot: ResultsSnapshot = ResultsSnapshot()
changed_paths: ChangedPaths = ChangedPaths()


# Functions
def splash_results() -> list[CommandResult]:
    return [
        cat_config_result,
        doctor_result,
        dump_config_result,
        git_log_result,
        git_remote_result,
        ignored_result,
        managed_dirs_result,
        managed_files_result,
        status_dirs_result,
        status_files_result,
        template_data_result,
    ]


def managed_cmd_results() -> list[CommandResult]:
    return [
        managed_dirs_result,
        managed_files_result,
        status_dirs_result,
        status_files_result,
    ]


def get_dest_dir() -> Path:
    return Path(parsed_dump_config["destDir"])


def _create_results_snapshot() -> ResultsSnapshot:
    managed_dirs = managed_dirs_result.std_out.splitlines()
    managed_files = managed_files_result.std_out.splitlines()
    status_dirs = status_dirs_result.std_out.splitlines()
    status_files = status_files_result.std_out.splitlines()

    return ResultsSnapshot(
        managed_paths={Path(line) for line in managed_dirs + managed_files if line},
        status_paths={Path(line[3:]): line[:2] for line in status_dirs + status_files},
    )


async def store_current_snapshot() -> None:
    global _managed_snapshot
    _managed_snapshot = _create_results_snapshot()


async def update_changed_paths() -> None:
    global changed_paths
    new_snapshot = _create_results_snapshot()
    removed_managed = _managed_snapshot.managed_paths - new_snapshot.managed_paths
    added_managed = new_snapshot.managed_paths - _managed_snapshot.managed_paths

    changed_status: dict[Path, tuple[str, str]] = {}

    intersection = _managed_snapshot.managed_paths & new_snapshot.managed_paths

    for path in intersection:
        old_code = _managed_snapshot.status_paths.get(path, "  ")
        new_code = new_snapshot.status_paths.get(path, "  ")

        if old_code != new_code:
            changed_status[path] = (old_code, new_code)

    changed_paths = ChangedPaths(
        added_managed=sorted(added_managed),
        changed_status=changed_status,
        removed_managed=sorted(removed_managed),
    )
