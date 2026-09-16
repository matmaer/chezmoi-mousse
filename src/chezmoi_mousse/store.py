from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from chezmoi_mousse import path_funcs
from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.named_tuples import (
    ChezmoiPaths,
    CmPathChanges,
    DumpConfigKeys,
    InitData,
)
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.named_tuples import CommandResult


init_data: InitData = InitData()
live_run: bool = False

add_ids = AppIds(BtnLabel.add)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)
logs_ids = AppIds(BtnLabel.logs)


man_tree_ids = AppIds(BtnLabel.operate)


cfg = DumpConfigKeys()

git_log_cr: CommandResult | None = None

cm_paths = ChezmoiPaths(
    chezmoi_dirs={},
    chezmoi_files={},
    managed_dirs={},
    managed_files={},
    status_dirs={},
    status_files={},
)

cm_path_changes = CmPathChanges(
    added_dirs={},
    added_files={},
    removed_dirs=[],
    removed_files=[],
    changed_dirs={},
    changed_files={},
    top_removed_dirs=[],
)


# Keep track of the selected path by tab
full_tree_path: Path | None = None
apply_path: Path | None = None
re_add_path: Path | None = None


async def update_cm_path_changes(
    new_man_dirs: dict[Path, str],
    new_man_files: dict[Path, str],
) -> None:

    global cm_paths
    old_man_dirs = copy.deepcopy(cm_paths.managed_dirs)
    old_man_files = copy.deepcopy(cm_paths.managed_files)

    def get_changes_dict(
        dict1: dict[Path, str], dict2: dict[Path, str]
    ) -> dict[Path, str]:
        return {
            key: dict2[key]
            for key in dict1.keys() & dict2.keys()
            if dict1[key] != dict2[key]
        }

    removed_dirs = [p for p in old_man_dirs if p not in new_man_dirs]

    global cm_path_changes

    cm_path_changes = CmPathChanges(
        added_dirs={p: s for p, s in new_man_dirs.items() if p not in old_man_dirs},
        added_files={p: s for p, s in new_man_files.items() if p not in old_man_files},
        removed_dirs=removed_dirs,
        removed_files=[p for p in old_man_files if p not in new_man_files],
        changed_dirs=get_changes_dict(old_man_dirs, new_man_dirs),
        changed_files=get_changes_dict(old_man_files, new_man_files),
        top_removed_dirs=path_funcs.get_sorted_top_parents(removed_dirs),
    )
