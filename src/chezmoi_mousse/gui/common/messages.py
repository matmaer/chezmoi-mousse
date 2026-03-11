from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult

    from .actionables import OpButton

__all__ = [
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "CmdResultMsg",
    "NewCmdResults",
    "OperateButtonMsg",
    "ProgressTextMsg",
]


class CurrentApplyNodeMsg(Message):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()


class CurrentReAddNodeMsg(Message):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()


class CmdResultMsg(Message):
    def __init__(self, cmd_result: CommandResult) -> None:
        self.cmd_result = cmd_result
        super().__init__()


class NewCmdResults(Message):
    def __init__(
        self,
        cmd_results: list[CommandResult],
        changed_root_paths: list[Path] | None = None,
    ) -> None:
        self.cmd_results = cmd_results
        self.changed_root_paths = changed_root_paths
        super().__init__()


class OperateButtonMsg(Message):
    def __init__(self, ids: AppIds, *, button: OpButton) -> None:
        self.button: OpButton = button
        self.ids = ids
        super().__init__()


class ProgressTextMsg(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()
