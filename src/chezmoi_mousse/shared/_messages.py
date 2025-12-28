from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:

    from chezmoi_mousse import (
        InitCloneData,
        NodeData,
        OpBtnEnum,
        ScreenName,
        TabName,
    )

__all__ = [
    "CloseButtonMsg",
    "CurrentAddNodeMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "InitCloneCmdMsg",
    "OperateButtonMsg",
]


class CloseButtonMsg(Message):
    def __init__(
        self,
        *,
        canvas_name: "TabName|ScreenName",
        pressed_label: str,
        tab_qid: str,
    ) -> None:
        self.canvas_name = canvas_name
        self.pressed_label = pressed_label
        self.tab_qid = tab_qid
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


class CurrentAddNodeMsg(Message):
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
        self,
        *,
        btn_enum: "OpBtnEnum",
        btn_qid: str,
        canvas_name: "TabName|ScreenName",
        pressed_label: str,
    ) -> None:
        self.btn_enum = btn_enum
        self.btn_qid = btn_qid
        self.canvas_name = canvas_name
        self.pressed_label = pressed_label
        super().__init__()
