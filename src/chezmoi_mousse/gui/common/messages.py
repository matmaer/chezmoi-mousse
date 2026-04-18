from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult


__all__ = ["LogCmdResultMsg", "CurrentNodeMsg", "ReadyToUseMsg"]


class LogCmdResultMsg(Message):
    def __init__(self, cmd_result: CommandResult) -> None:
        self.cmd_result = cmd_result
        super().__init__()


class CurrentNodeMsg(Message):
    def __init__(self, path: Path, ids: AppIds) -> None:
        self.ids = ids
        self.path = path
        super().__init__()


class ReadyToUseMsg(Message): ...
