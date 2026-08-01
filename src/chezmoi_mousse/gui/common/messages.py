from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.cm_types import AppIds, CommandResult


__all__ = ["LogCmdResultMsg", "CurrentNodeMsg"]


class LogCmdResultMsg(Message):
    def __init__(self, cmd_result: CommandResult) -> None:
        self.cmd_result = cmd_result
        super().__init__()


class CurrentNodeMsg(Message):
    def __init__(
        self,
        *,
        ids: AppIds,
        path: Path,
        no_changed_paths: bool,
        has_status: bool,
        is_ndir: bool,
        dest_dir: Path,
    ) -> None:
        self.ids = ids
        self.path = path
        self.no_changed_paths = no_changed_paths
        self.has_status = has_status
        self.is_ndir = is_ndir
        self._dest_dir = dest_dir
        super().__init__()

    @property
    def border_path(self) -> str:
        rel_path_border = f" {self.path.relative_to(self._dest_dir)} "
        return rel_path_border if self.path != self._dest_dir else f" {self._dest_dir} "

    @property
    def is_dest_dir(self) -> bool:
        return self.path == self._dest_dir
