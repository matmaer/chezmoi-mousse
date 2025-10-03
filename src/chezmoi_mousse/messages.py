from dataclasses import dataclass, field
from pathlib import Path

from textual.message import Message

from chezmoi_mousse.id_typing import NodeData
from chezmoi_mousse.id_typing.enums import (
    OperateBtn,
    OperateHelp,
    TabName,
    TreeName,
)


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
    node_data: NodeData
    node_parent: NodeData
    node_leaves: list[NodeData] = field(default_factory=list[NodeData])
    node_subdirs: list[NodeData] = field(default_factory=list[NodeData])


class TreeNodeDataMsg(Message):
    def __init__(self, node_context: TreeNodeData) -> None:
        self.node_context = node_context
        super().__init__()


@dataclass
class OperateBtnPressedData:
    tab_name: TabName
    operate_help: OperateHelp
    tree_node_data: TreeNodeData


class OperateBtnDataMsg(Message):

    def __init__(self, btn_data: OperateBtnPressedData) -> None:
        self.btn_data = btn_data
        super().__init__()
