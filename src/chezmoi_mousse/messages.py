from dataclasses import dataclass, field
from pathlib import Path

from id_typing import DirNodeData, FileNodeData, OperateBtn, TabName, TreeName
from textual.message import Message


@dataclass
class OperateData:
    path: Path | None = None
    operation_executed: bool = False
    tab_name: TabName | None = None
    found: bool | None = None
    button_name: OperateBtn | None = None
    is_file: bool | None = None


class OperateDataMsg(Message):
    def __init__(self, dismiss_data: OperateData) -> None:
        self.dismiss_data: OperateData = dismiss_data
        super().__init__()


@dataclass
class TreeNodeData:
    tree_name: TreeName
    node_data: DirNodeData | FileNodeData
    node_parent: DirNodeData | None = None
    node_leaves: list[FileNodeData] = field(default_factory=list[FileNodeData])
    node_subdirs: list[DirNodeData] = field(default_factory=list[DirNodeData])


class TreeNodeDataMsg(Message):
    def __init__(self, node_context: TreeNodeData) -> None:
        self.node_context = node_context
        super().__init__()
