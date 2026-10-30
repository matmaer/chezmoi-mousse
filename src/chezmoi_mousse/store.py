from __future__ import annotations

from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.chezmoi_paths import CmPathChanges
from chezmoi_mousse.data_types import ParsedDumpConfig
from chezmoi_mousse.str_enums import BtnLabel, ColorVar

if TYPE_CHECKING:
    from chezmoi_mousse.chezmoi_paths import ChezmoiTreePaths
    from chezmoi_mousse.data_types import InitData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

init_data: InitData

op_ids = AppIds(BtnLabel.operate)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)


cfg: ParsedDumpConfig

cm_paths: ChezmoiTreePaths

cm_changes: CmPathChanges

_first_change_calculation: bool = True


async def handle_new_tree_paths(
    app: ChezmoiGui, new_tree_paths: ChezmoiTreePaths
) -> None:
    global cm_paths
    global cm_changes
    global _first_change_calculation

    old_tree_paths = new_tree_paths if _first_change_calculation else cm_paths

    cm_changes = CmPathChanges(
        _old_tree_paths=old_tree_paths, _new_tree_paths=new_tree_paths
    )
    cm_paths = new_tree_paths
    _first_change_calculation = False
    app.logs_tab.mount_line(
        "Updated cm_paths and cm_changes in store.py", ColorVar.secondary
    )


async def decode_and_store_config(std_out: str) -> None:
    global cfg
    cfg = ParsedDumpConfig(_dump_config_std_out=std_out)
