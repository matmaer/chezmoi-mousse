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


class TreeNodeSelectedMsg(Message):
    def __init__(
        self,
        node_data: NodeData | None = None,
        node_leaves: list[NodeData] | None = None,
        node_parent: NodeData | None = None,
        node_subdirs: list[NodeData] | None = None,
        tree_name: TreeName | None = None,
    ) -> None:
        self.node_data = node_data
        self.node_leaves = node_leaves if node_leaves is not None else []
        self.node_parent = node_parent
        self.node_subdirs = node_subdirs if node_subdirs is not None else []
        self.tree_name = tree_name
        super().__init__()


class OperateBtnPressedMsg(Message):

    def __init__(
        self,
        tab_name: TabName | None = None,
        operate_help: OperateHelp | None = None,
    ) -> None:
        self.tab_name = tab_name
        self.operate_help = operate_help
        super().__init__()
