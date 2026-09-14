from __future__ import annotations

from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.data_classes import ChezmoiPaths
from chezmoi_mousse.named_tuples import DumpConfigKeys, InitData
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.named_tuples import CommandResult


init_data: InitData = InitData()
pre_mount: bool = True
live_run: bool = False

add_ids = AppIds(BtnLabel.add)
apply_ids = AppIds(BtnLabel.apply)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)
logs_ids = AppIds(BtnLabel.logs)
re_add_ids = AppIds(BtnLabel.re_add)


man_tree_ids = AppIds(BtnLabel.managed_pane)
danger_zone_ids = AppIds(BtnLabel.danger_pane)


cfg = DumpConfigKeys()

git_log_cr: CommandResult | None = None

cm_paths = ChezmoiPaths(
    managed_dirs={},
    managed_files={},
    status_dirs={},
    status_files={},
    old_man_dirs={},
    old_man_files={},
    old_status_dirs={},
    old_status_files={},
)

# Keep track of the selected path by tab
add_path: Path | None = None
apply_path: Path | None = None
re_add_path: Path | None = None


def get_tab_path(btn_label: BtnLabel) -> Path | None:
    if btn_label == BtnLabel.add_run:
        return add_path
    elif btn_label == BtnLabel.apply_run:
        return apply_path
    elif btn_label == BtnLabel.re_add_run:
        return re_add_path
    else:
        raise ValueError(f"Invalid button label: {btn_label}")
