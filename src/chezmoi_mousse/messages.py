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


class OperateDismissMsg(Message):
    def __init__(
        self,
        button_name: OperateBtn | None = None,
        found: bool | None = None,
        operation_executed: bool | None = None,
        path: Path | None = None,
        tab_name: TabName | None = None,
    ) -> None:
        self.button_name = button_name
        self.found = found
        self.operation_executed = operation_executed
        self.path = path
        self.tab_name = tab_name
        super().__init__()


@dataclass
class TreeNodeSelectedData:
    tree_name: TreeName
    node_data: NodeData
    node_parent: NodeData
    node_leaves: list[NodeData] = field(default_factory=list[NodeData])
    node_subdirs: list[NodeData] = field(default_factory=list[NodeData])


class TreeNodeSelectedMsg(Message):
    def __init__(self, node_context: TreeNodeSelectedData) -> None:
        self.node_context = node_context
        super().__init__()


@dataclass
class OperateBtnPressedData:
    tab_name: TabName
    operate_help: OperateHelp
    tree_node_data: TreeNodeSelectedData


class OperateBtnPressedMsg(Message):

    def __init__(self, btn_data: OperateBtnPressedData) -> None:
        self.btn_data = btn_data
        super().__init__()
