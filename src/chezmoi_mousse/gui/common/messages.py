from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from chezmoi_mousse.data_types import CommandResult


__all__ = [
    "CommandResultMsg",
    "ShowTreeQidMsg",
]


class CommandResultMsg(Message):
    def __init__(self, results: CommandResult) -> None:
        self.cmd_result: CommandResult = results
        super().__init__()


class ShowTreeQidMsg(Message):
    def __init__(self, tree_id_q: str) -> None:
        self.tree_id_q = tree_id_q
        super().__init__()
