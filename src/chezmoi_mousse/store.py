from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.chezmoi_paths import (
    ChezmoiTreePaths,
    CmPathChanges,
)
from chezmoi_mousse.named_tuples import (
    DumpConfigKeys,
    InitData,
)
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from chezmoi_mousse.chezmoi_paths import (
        ChezmoiTreePaths,
    )
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

init_data: InitData = InitData()
live_run: bool = False

op_ids = AppIds(BtnLabel.operate)
logs_ids = AppIds(BtnLabel.logs)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)


cfg = DumpConfigKeys()

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
    # Set store.cfg variable
    parsed_std_out = json.loads(std_out)
    global cfg
    cfg = DumpConfigKeys(
        dest_dir_path=Path(parsed_std_out["destDir"]),
        auto_add_bool=parsed_std_out["git"]["autoadd"],
        auto_commit_bool=parsed_std_out["git"]["autocommit"],
        auto_push_bool=parsed_std_out["git"]["autopush"],
    )
