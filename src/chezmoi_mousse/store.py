from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.named_tuples import CommandResult


init_data: InitData = InitData()
live_run: bool = False

operate_ids = AppIds(BtnLabel.operate)
logs_ids = AppIds(BtnLabel.logs)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)


cfg = DumpConfigKeys()

git_log_cr: CommandResult | None = None


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


# Keep track of the selected path by tab
full_tree_path: Path | None = None
apply_path: Path | None = None
re_add_path: Path | None = None


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
