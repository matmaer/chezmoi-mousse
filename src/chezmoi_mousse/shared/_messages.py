from typing import TYPE_CHECKING

from textual.message import Message

from chezmoi_mousse._chezmoi import WriteCmd

if TYPE_CHECKING:

    from chezmoi_mousse import NodeData, OperateBtn, ScreenName, TabName

__all__ = [
    "CurrentAddNodeMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "InitCommandMsg",
    "OperateButtonMsg",
]

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
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class InitCommandMsg(Message):
    def __init__(
        self, init_cmd: "WriteCmd", init_arg: str, valid_arg: bool
    ) -> None:
        self.init_cmd = init_cmd
        self.init_arg = init_arg
        self.valid_arg = valid_arg
        super().__init__()


class OperateButtonMsg(Message):
    def __init__(
        self,
        *,
        btn_enum: "OperateBtn",
        label: "str",
        tooltip: "str",
        canvas_name: "TabName|ScreenName",
    ) -> None:
        self.btn_enum = btn_enum
        self.label = label
        self.tooltip = tooltip
        self.canvas_name = canvas_name
        super().__init__()
