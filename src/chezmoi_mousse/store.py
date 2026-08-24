from __future__ import annotations

from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.cm_dataclasses import Changed
from chezmoi_mousse.named_tuples import CommandResult, ParsedDumpConfig
from chezmoi_mousse.str_enums import OpBtnLabel, TabLabel

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.cm_types import StatusPairs


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

paths = Changed()

managed_dirs: set[Path] = set()
managed_files: set[Path] = set()
status_dirs: StatusPairs = {}
status_files: StatusPairs = {}

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
