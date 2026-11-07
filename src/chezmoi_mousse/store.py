from __future__ import annotations

import tempfile
import traceback
from datetime import datetime
from pathlib import Path
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


async def store_new_tree_paths(
    app: ChezmoiGui, new_tree_paths: ChezmoiTreePaths
) -> None:
    global cm_paths
    global cm_changes
    global _first_change_calculation

    old_tree_paths = new_tree_paths if _first_change_calculation else cm_paths
    cm_changes = CmPathChanges(
        _old_tree_paths=old_tree_paths, _new_tree_paths=new_tree_paths
    )
    _first_change_calculation = False
    cm_paths = new_tree_paths

    app.logs_tab.mount_line(
        "Updated cm_paths and cm_changes in store.py", ColorVar.secondary
    )


async def decode_and_store_config(std_out: str) -> None:
    global cfg
    cfg = ParsedDumpConfig(dump_config_std_out=std_out)


def save_stacktrace() -> None:
    def _new_log_path(out_dir: Path) -> Path:
        return out_dir / f"{datetime.now().strftime('%Y%m%d_%Hh_%Mm_%Ss')}.log"

    try:
        out_dir = Path(tempfile.gettempdir()) / "chezmoi_mousse_stacktraces"
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return

    to_write = traceback.format_exc().strip()

    all_log_files = [p for p in out_dir.glob("*.log") if p.is_file()]
    log_files = [p for p in all_log_files if not p.name.startswith("backup_")]
    log_files = sorted(log_files, key=lambda p: p.name, reverse=True)

    if not log_files:
        log_file = _new_log_path(out_dir)
    else:
        log_file = log_files[0]
        with log_file.open("r") as f:
            old_contents = f.read().strip()
        if old_contents == to_write:
            log_file.rename(_new_log_path(out_dir))
            return  # Renamed existing log in-place: no new write is needed

    log_file.rename(log_file.with_name(f"backup_{log_file.name}"))
    # clean up old backups, keeping only the five most recent ones
    backups = sorted(out_dir.glob("backup_*"), key=lambda p: p.name, reverse=True)
    for old_backup in backups[5:]:
        old_backup.unlink(missing_ok=True)
    new_log_path = _new_log_path(out_dir)
    with new_log_path.open("w") as f:
        f.write(to_write)
