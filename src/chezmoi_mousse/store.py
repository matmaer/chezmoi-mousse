from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.named_tuples import CommandResult, ParsedDumpConfig
from chezmoi_mousse.str_enums import OpBtnLabel, TabLabel

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


add_id = AppIds(TabLabel.add)
apply_id = AppIds(TabLabel.apply)
config_id = AppIds(TabLabel.config)
debug_id = AppIds(TabLabel.debug)
logs_id = AppIds(TabLabel.logs)
re_add_id = AppIds(TabLabel.re_add)

cfg = ParsedDumpConfig()

cat_config_result = CommandResult.empty()
doctor_result = CommandResult.empty()
dump_config_result = CommandResult.empty()
git_log_result = CommandResult.empty()
git_remote_result = CommandResult.empty()
ignored_result = CommandResult.empty()
managed_dirs_result = CommandResult.empty()
managed_files_result = CommandResult.empty()
status_dirs_result = CommandResult.empty()
status_files_result = CommandResult.empty()
template_data_result = CommandResult.empty()

parsed_template_data: ParsedJson = {}

_managed_snapshot: ResultsSnapshot = ResultsSnapshot()
changed_paths: ChangedPaths = ChangedPaths()

# Keep track of the selected path by tab
add_path: Path | None = None
apply_path: Path | None = None
re_add_path: Path | None = None


def get_tab_path(btn_label: OpBtnLabel) -> Path | None:
    if btn_label == OpBtnLabel.add_run:
        return add_path
    elif btn_label == OpBtnLabel.apply_run:
        return apply_path
    elif btn_label == OpBtnLabel.re_add_run:
        return re_add_path
    else:
        raise ValueError(f"Invalid button label: {btn_label}")


def _create_results_snapshot() -> ResultsSnapshot:
    managed_dirs = managed_dirs_result.std_out.splitlines()
    managed_files = managed_files_result.std_out.splitlines()
    status_dirs = status_dirs_result.std_out.splitlines()
    status_files = status_files_result.std_out.splitlines()

    return ResultsSnapshot(
        managed_paths={Path(line) for line in managed_dirs + managed_files if line},
        status_paths={Path(line[3:]): line[:2] for line in status_dirs + status_files},
    )


def store_current_snapshot() -> None:
    global _managed_snapshot
    _managed_snapshot = _create_results_snapshot()


def update_changed_paths() -> None:
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
