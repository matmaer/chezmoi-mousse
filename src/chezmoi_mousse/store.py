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

st_dir: Path | None = None

try:
    st_dir = Path(tempfile.gettempdir()) / "chezmoi_mousse_stacktraces"
    st_dir.mkdir(exist_ok=True)
except OSError:
    pass

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
    new_tree_paths.reload_un_man_children(old_tree_paths)
    new_tree_paths.reuse_unchanged_node_data(old_tree_paths)
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
    if st_dir is None:
        return

    def _current_timestamp_name() -> str:
        return f"{datetime.now().strftime('%Y%m%d_%Hh_%Mm_%Ss')}.log"

    def _write_log_file(st_dir: Path) -> None:
        to_write = traceback.format_exc().strip()
        new_log_path = st_dir / _current_timestamp_name()
        with new_log_path.open("w") as f:
            f.write(to_write)

    to_write = traceback.format_exc().strip()
    all_logs = [p for p in st_dir.glob("*.log") if p.is_file()]
    current_logs = [p for p in all_logs if not p.name.startswith("backup_")]

    if current_logs and len(current_logs) > 1:
        sorted_logs = sorted(current_logs, key=lambda p: p.name, reverse=True)
        to_delete = sorted_logs[1:]
        for old_log in to_delete:
            old_log.unlink(missing_ok=True)
            current_logs.remove(old_log)
    elif not current_logs:
        _write_log_file(st_dir)
        return

    current_log = current_logs[0]
    with current_log.open("r") as f:
        if f.read().strip() == to_write:
            current_log.rename(st_dir / _current_timestamp_name())
        else:
            current_log.rename(st_dir / f"backup_{current_log.name}")
            _write_log_file(st_dir)

    # clean up backups
    backup_logs = [p for p in all_logs if p.name.startswith("backup_")]
    if len(backup_logs) > 5:
        backup_logs = sorted(backup_logs, key=lambda p: p.name, reverse=True)
        to_delete = backup_logs[5:]
        for bu_path in to_delete:
            bu_path.unlink(missing_ok=True)
