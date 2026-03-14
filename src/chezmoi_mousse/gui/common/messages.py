from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CommandResult


__all__ = ["LogCmdResultMsg", "CurrentApplyNodeMsg", "CurrentReAddNodeMsg"]


class LogCmdResultMsg(Message):
    def __init__(self, cmd_result: CommandResult) -> None:
        self.cmd_result = cmd_result
        super().__init__()


class CurrentApplyNodeMsg(Message):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()


class CurrentReAddNodeMsg(Message):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()
