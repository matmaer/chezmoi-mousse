from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:

    from chezmoi_mousse import (
        DiffData,
        InitCloneData,
        NodeData,
        OperateBtn,
        ScreenName,
        TabName,
    )

__all__ = [
    "CurrentAddNodeMsg",
    "CurrentApplyDiffMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddDiffMsg",
    "CurrentReAddNodeMsg",
    "InitCloneCmdMsg",
    "OperateButtonMsg",
]

# messages used to keep track in main screen to push the operate screen with
# the correct data


class CurrentApplyDiffMsg(Message):
    def __init__(self, diff_data: "DiffData") -> None:
        self.diff_data = diff_data
        super().__init__()


class CurrentApplyNodeMsg(Message):
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentReAddDiffMsg(Message):
    def __init__(self, diff_data: "DiffData") -> None:
        self.diff_data = diff_data
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
        btn_enum: "OperateBtn",
        label: "str",
        canvas_name: "TabName|ScreenName",
    ) -> None:
        self.btn_enum = btn_enum
        self.label = label
        self.canvas_name = canvas_name
        super().__init__()
