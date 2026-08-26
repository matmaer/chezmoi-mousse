from __future__ import annotations

import os
import queue
import sys
import tracemalloc
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.data_classes import Changed, ChezmoiRepoChecks, StatusPaths
from chezmoi_mousse.named_tuples import (
    ParsedDumpConfig,
)
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.named_tuples import CommandResult
    from chezmoi_mousse.str_enums import PathKind, StatusCode


PILOT_MODE = (
    os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1" or "--pilot-mode" in sys.argv
)

SHOW_DEBUG_TAB = (
    "--dev" in sys.argv
    or "devtools" in os.getenv("TEXTUAL", "").split(",")
    or "--show-debugtab" in sys.argv
    or PILOT_MODE
)

if SHOW_DEBUG_TAB:
    tracemalloc.start()

results_queue: queue.Queue[CommandResult] = queue.Queue()

live_run: bool = False

add_ids = AppIds(BtnLabel.add)
apply_ids = AppIds(BtnLabel.apply)
config_ids = AppIds(BtnLabel.config)
debug_ids = AppIds(BtnLabel.debug)
logs_ids = AppIds(BtnLabel.logs)
re_add_ids = AppIds(BtnLabel.re_add)

cfg = ParsedDumpConfig()
cm_repo_checks = ChezmoiRepoChecks()

changed = Changed()


managed_dirs: dict[Path, PathKind] = {}
managed_files: dict[Path, PathKind] = {}
status_dirs_kind: dict[Path, PathKind] = {}
status_files_kind: dict[Path, PathKind] = {}

dir_status_pairs: dict[Path, str] = {}
file_status_pairs: dict[Path, str] = {}

apply_status_dirs: dict[Path, StatusCode] = {}
apply_status_files: dict[Path, StatusCode] = {}
re_add_status_dirs: dict[Path, StatusCode] = {}
re_add_status_files: dict[Path, StatusCode] = {}

apply_paths = StatusPaths(dirs=apply_status_dirs, files=apply_status_files)
re_add_paths = StatusPaths(dirs=re_add_status_dirs, files=re_add_status_files)


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
