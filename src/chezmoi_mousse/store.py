from __future__ import annotations

from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.data_classes import ChezmoiPaths
from chezmoi_mousse.named_tuples import DumpConfigKeys, InitData
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
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

cm_paths = ChezmoiPaths.empty()
