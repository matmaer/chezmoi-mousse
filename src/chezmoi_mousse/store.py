from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.data_classes import Changed, ManagedPaths
from chezmoi_mousse.named_tuples import DumpConfigKeys, InitData
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from pathlib import Path


class ManagedCmdResults:
    """Simple container to collect managed command results, it's simply the output of
    the command on stdout."""

    managed_dirs_result: ClassVar[str] = ""
    managed_files_result: ClassVar[str] = ""
    status_dirs_result: ClassVar[str] = ""
    status_files_result: ClassVar[str] = ""


init_data: InitData = InitData()
pre_mount: bool = True
live_run: bool = False

add_ids = AppIds(BtnLabel.add)
apply_ids = AppIds(BtnLabel.apply)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)
logs_ids = AppIds(BtnLabel.logs)
re_add_ids = AppIds(BtnLabel.re_add)

cfg = DumpConfigKeys()

changed = Changed()
paths = ManagedPaths()

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
