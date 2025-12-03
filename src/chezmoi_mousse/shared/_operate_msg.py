from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:

    from chezmoi_mousse import DirTreeNodeData, NodeData

__all__ = ["CurrentAddNodeMsg", "CurrentApplyNodeMsg", "CurrentReAddNodeMsg"]

# messages used to keep track in main screen to push the operate screen with
# the correct data


class CurrentApplyNodeMsg(Message):
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentReAddNodeMsg(Message):
    # used to keep track in main screen to push the operate screen
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentAddNodeMsg(Message):
    # used to keep track in main screen to push the operate screen
    def __init__(self, dir_tree_node_data: "DirTreeNodeData") -> None:
        self.dir_tree_node_data = dir_tree_node_data
        super().__init__()


class InitCompletedMsg(Message):
    pass
