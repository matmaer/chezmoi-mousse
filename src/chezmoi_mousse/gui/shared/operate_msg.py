from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import NodeData

__all__ = ["CurrentOperatePathMsg", "TreeNodeSelectedMsg"]


class CurrentOperatePathMsg(Message):
    def __init__(self, path: "Path") -> None:
        self.path = path
        super().__init__()


class TreeNodeSelectedMsg(Message):
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()
