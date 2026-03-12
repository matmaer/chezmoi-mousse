from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult

    from .actionables import OpButton
    from .loading_modal import LoadingModalResult

__all__ = [
    "LoadingResultMsg",
    "LogCmdResultMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "OperateButtonMsg",
]


class LoadingResultMsg(Message):
    def __init__(self, loading_result: LoadingModalResult) -> None:
        self.loading_result = loading_result
        super().__init__()


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


class OperateButtonMsg(Message):
    def __init__(self, ids: AppIds, *, button: OpButton) -> None:
        self.button: OpButton = button
        self.ids = ids
        super().__init__()
