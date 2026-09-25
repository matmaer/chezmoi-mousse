from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.chezmoi_paths import (
    ChezmoiTreePaths,
    CmOpButtonSets,
    CmPathChanges,
)
from chezmoi_mousse.named_tuples import (
    DumpConfigKeys,
    InitData,
)
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

init_data: InitData = InitData()
live_run: bool = False

op_ids = AppIds(BtnLabel.operate)
logs_ids = AppIds(BtnLabel.logs)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)


cfg = DumpConfigKeys()


cm_paths = ChezmoiTreePaths(
    _status_dirs_pcr={},
    _status_files_pcr={},
    _un_man_dir_set=frozenset(),
    _un_man_file_set=frozenset(),
    man_dir_set=frozenset(),
    man_file_set=frozenset(),
    man_path_set=frozenset(),
    missing_managed=frozenset(),
    status_dir_set=frozenset(),
    status_file_set=frozenset(),
    status_path_set=frozenset(),
)


cm_changes = CmPathChanges(
    _old_tree_paths=cm_paths,
    _new_tree_paths=cm_paths,
)

op_btn_sets = CmOpButtonSets(cm_paths)


async def handle_new_tree_paths(
    app: ChezmoiGui,
    new_tree_paths: ChezmoiTreePaths,
) -> None:

    global cm_paths
    global cm_changes
    global op_btn_sets
    cm_changes = CmPathChanges(
        _old_tree_paths=cm_paths,
        _new_tree_paths=new_tree_paths,
    )

    cm_paths = new_tree_paths
    op_btn_sets = CmOpButtonSets(new_tree_paths)
    app.app_log.write_app_log_msg(
        "Updated cm_paths, cm_changes and op_btn_sets in store.py"
    )


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
