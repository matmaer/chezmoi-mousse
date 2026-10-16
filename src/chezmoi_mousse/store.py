from __future__ import annotations

from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.chezmoi_paths import CmPathChanges
from chezmoi_mousse.data_types import (
    InitData,
    ParsedDumpConfig,
)
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from chezmoi_mousse.chezmoi_paths import ChezmoiTreePaths
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

init_data: InitData = InitData()
live_run: bool = False

op_ids = AppIds(BtnLabel.operate)
logs_ids = AppIds(BtnLabel.logs)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)


cfg: ParsedDumpConfig

cm_paths: ChezmoiTreePaths

cm_changes: CmPathChanges | None = None


async def handle_new_tree_paths(
    app: ChezmoiGui,
    new_tree_paths: ChezmoiTreePaths,
) -> None:

    global cm_paths
    global cm_changes

    cm_changes = CmPathChanges(
        _old_tree_paths=new_tree_paths if cm_changes is None else cm_paths,
        _new_tree_paths=new_tree_paths,
    )

    cm_paths = new_tree_paths
    app.app_log.write_app_log_msg("Updated cm_paths and cm_changes in store.py")


async def decode_and_store_config(std_out: str) -> None:
    global cfg
    cfg = ParsedDumpConfig(_dump_config_std_out=std_out)
