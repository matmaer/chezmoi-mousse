from textual.message import Message

from chezmoi_mousse.id_typing import CurrentTreeNodes, OperateData


class OperateMessage(Message):
    def __init__(self, dismiss_data: OperateData) -> None:
        self.dismiss_data: OperateData = dismiss_data
        super().__init__()


class CurrentTreeNodesMessage(Message):
    def __init__(self, current_tree_nodes: CurrentTreeNodes) -> None:
        self.current_tree_nodes = current_tree_nodes
        super().__init__()
