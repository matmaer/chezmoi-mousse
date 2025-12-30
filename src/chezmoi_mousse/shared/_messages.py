from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:

    from chezmoi_mousse import AppIds, InitCloneData, NodeData

    from ._actionables import CloseButton, OpButton

__all__ = [
    "CloseButtonMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "InitCloneCmdMsg",
    "OperateButtonMsg",
]


class CloseButtonMsg(Message):
    def __init__(self, *, button: "CloseButton", ids: "AppIds") -> None:
        self.button = button
        self.ids = ids
        super().__init__()


class CurrentApplyNodeMsg(Message):
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentReAddNodeMsg(Message):
    # used to keep track in main screen to push the operate screen
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class InitCloneCmdMsg(Message):
    def __init__(self, init_clone_data: "InitCloneData") -> None:
        self.init_clone_data = init_clone_data
        super().__init__()


class OperateButtonMsg(Message):
    def __init__(
        self, *, button: "OpButton", ids: "AppIds", pressed_label: str
    ) -> None:
        self.button = button
        self.ids = ids
        self.pressed_label = pressed_label
        super().__init__()
