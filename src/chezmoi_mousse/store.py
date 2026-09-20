from __future__ import annotations

import json
from pathlib import Path

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.chezmoi_paths import (
    ChezmoiPathSets,
    ChezmoiTreePaths,
    CmPathChanges,
)
from chezmoi_mousse.named_tuples import (
    DumpConfigKeys,
    InitData,
)
from chezmoi_mousse.str_enums import BtnLabel

init_data: InitData = InitData()
live_run: bool = False

op_ids = AppIds(BtnLabel.operate)
logs_ids = AppIds(BtnLabel.logs)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)


cfg = DumpConfigKeys()


cm_paths = ChezmoiTreePaths(
    _man_dirs_list=[],
    _man_files_list=[],
    _status_dirs_list=[],
    _status_files_list=[],
    _unman_dirs_list=[],
    _unman_files_list=[],
)

cm_path_sets: ChezmoiPathSets = ChezmoiPathSets(
    _cm_paths=ChezmoiTreePaths(
        _man_dirs_list=[],
        _man_files_list=[],
        _status_dirs_list=[],
        _status_files_list=[],
        _unman_dirs_list=[],
        _unman_files_list=[],
    )
)

cm_changes = CmPathChanges(
    _old_tree_paths=ChezmoiTreePaths(
        _man_dirs_list=[],
        _man_files_list=[],
        _status_dirs_list=[],
        _status_files_list=[],
        _unman_dirs_list=[],
        _unman_files_list=[],
    ),
    _new_tree_paths=ChezmoiTreePaths(
        _man_dirs_list=[],
        _man_files_list=[],
        _status_dirs_list=[],
        _status_files_list=[],
        _unman_dirs_list=[],
        _unman_files_list=[],
    ),
)


async def handle_new_tree_paths(
    new_tree_paths: ChezmoiTreePaths,
) -> None:

    global cm_paths
    global cm_changes
    global cm_path_sets

    cm_changes = CmPathChanges(
        _old_tree_paths=cm_paths,
        _new_tree_paths=new_tree_paths,
    )
    # The differences are calculated, now overwrite the store.tree_paths
    cm_path_sets = ChezmoiPathSets(_cm_paths=new_tree_paths)
    cm_paths = new_tree_paths


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
